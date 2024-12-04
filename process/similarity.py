import requests
import spacy
import psycopg
import os
from urllib.parse import urlparse
from time import sleep, time

def process_similarity():
  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT (id, readme_url, repo_url) FROM ships")
      ships = cur.fetchall()

  if len(ships) == 0:
    print("Ships not downloaded.")
    return
  
  filtered_ships = {}

  nlp = spacy.load("en_core_web_md")
  normalized_list = []
  id_list = []
  languages = []
  print("Downloading & normalizing ship READMEs & GitHub data...")
  for row in ships:
    ship = row[0]
    try:
      readme_text = requests.get(ship[1])
    except:
      print(f"Skipping ship record {ship[0]} as it does not have a valid README")
      continue

    if readme_text.status_code != 200:
      print(f"Skipping ship record {ship[0]} as it does not have a valid README")
      continue

    if readme_text.text == "":
      print(f"Skipping ship record {ship[0]} as it has an empty README")
      continue

    normalized = readme_text.text[0:5000]
    embedding = nlp(normalized)

    normalized_list.append(embedding)

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
          languages.append(None)
        else:
          languages.append(dict(languages_req.json()))
      except:
        languages.append(None)
    else:
      languages.append(None)

    id_list.append(ship[0])
    filtered_ships[ship[0]] = ship

  print("Calculating similarity...")

  print("Building similarity pairs...")
  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("DELETE FROM similarity")

      insertArgs = []
      for x in range(len(id_list)):
        for y in range(len(id_list)):
          if x == y:
            continue
            
          ai_value = normalized_list[x].similarity(normalized_list[y])

          lang_similarity = 0
          if languages[x] != None and languages[y] != None:
            if len(languages[x].keys()) != 0 and len(languages[y].keys()) != 0:
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
              
              lang_similarity = int(top_language_y == top_language_x)
          
          insertArgs.append((id_list[x], id_list[y], ai_value, lang_similarity))
    
      updateArgs = []
      for ship in filtered_ships:
        updateArgs.append((ship,))
        
      cur.executemany("INSERT INTO similarity (shipa, shipb, nlp_value, lang_value) VALUES (%s, %s, %s, %s)", insertArgs)
      cur.executemany("UPDATE ships SET filtered = true WHERE id = %s", updateArgs)
    
    conn.commit()

  print("Done with similarity")