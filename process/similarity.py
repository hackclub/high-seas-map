import requests
import psycopg
import os
from urllib.parse import urlparse
from time import sleep, time
from joblib import Parallel, delayed

def process_similarity(pre_ships):
  if pre_ships != None:
    ships = list(map(lambda s: ((s["id"], s["fields"]["readme_url"], s["fields"]["repo_url"]),), pre_ships))
  else:
    with psycopg.connect(os.environ["DB_URI"]) as conn:
      with conn.cursor() as cur:
        cur.execute("SELECT (id, readme_url, repo_url) FROM ships")
        ships = cur.fetchall()

        cur.close()
    
    conn.close()

  if len(ships) == 0:
    print("Ships not downloaded.")
    return
  
  filtered_ships = {}
  languages = {}
  print("Downloading ship GitHub data...")

  def download_data(ship):
    ship_languages = None
    parsed_url = urlparse(ship[2])
    if parsed_url.netloc == "github.com":
      path = parsed_url.path.split("/")
      headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': "2022-11-28",
        'Authorization': f"Bearer {os.environ["GITHUB_TOKEN"]}"
      }
      try:
        languages_req = requests.get(f"https://api.github.com/repos/{path[1]}/{path[2]}/languages", headers=headers)
        while (languages_req.status_code == 429) or (languages_req.status_code == 403):
          reset_time = int(languages_req.headers["x-ratelimit-reset"])
          time_left = reset_time - time()
          print(f"github ratelimited... waiting {time_left} seconds")
          sleep(time_left)

          languages_req = requests.get(f"https://api.github.com/repos/{path[1]}/{path[2]}/languages", headers=headers)
        if languages_req.status_code != 200:
          print(languages_req.json())
        else:
          ship_languages = dict(languages_req.json())
      except:
        print(f"error when fetching languages for {ship[0]}")

    return (ship, ship_languages)
  
  ships_result = Parallel(n_jobs=5)(delayed(download_data)(row[0]) for row in ships)
  for ship_res in ships_result:
    filtered_ships[ship_res[0][0]] = ship_res[0]
    languages[ship_res[0][0]] = ship_res[1]

  print("Calculating similarity...")

  print("Building similarity pairs...")

  insertArgs = []
  for x in filtered_ships.keys():
    for y in filtered_ships.keys():
      if x == y:
        continue

      top_lang_similarity = 0
      lang_similarity = 0
      if languages[x] != None and languages[y] != None:
        if len(languages[x].keys()) != 0 and len(languages[y].keys()) != 0:
          ship_languages = set(languages[x].keys()).union(set(languages[y].keys()))
          lang_overlap = {}
          total_x = sum(languages[x].values())
          total_y = sum(languages[y].values())

          for lang in ship_languages:
            if lang in languages[x]:
              percent_x = languages[x][lang] / total_x
            else:
              percent_x = 0
            if lang in languages[y]:
              percent_y = languages[y][lang] / total_y
            else:
              percent_y = 0
            
            lang_overlap[lang] = min(0, min(percent_x, percent_y))

          lang_similarity = sum(lang_overlap.values()) / len(lang_overlap.keys())

          top_language_x = None
          for lang in languages[x]:
            if top_language_x == None:
              top_language_x = lang
            elif languages[x][lang] > languages[x][top_language_x]:
              top_language_x = lang
          
          top_language_y = None
          for lang in languages[y]:
            if top_language_y == None:
              top_language_y = lang
            elif languages[y][lang] > languages[y][top_language_y]:
              top_language_y = lang
          
          top_lang_similarity = int(top_language_y == top_language_x)
      
      insertArgs.append((x, y, top_lang_similarity, lang_similarity))

  updateArgs = []
  for ship_res in filtered_ships:
    updateArgs.append((ship_res,))

  print("Done with similarity")
  if pre_ships != None:
    return (insertArgs, list(filtered_ships.keys()))
  else:
    with psycopg.connect(os.environ["DB_URI"]) as conn:
      with conn.cursor() as cur:
        cur.execute("DELETE FROM similarity")  
        cur.executemany("INSERT INTO similarity (shipa, shipb, top_lang_value, lang_value) VALUES (%s, %s, %s, %s)", insertArgs)
        cur.executemany("UPDATE ships SET filtered = true WHERE id = %s", updateArgs)

        cur.close()
      
      conn.commit()
      conn.close()