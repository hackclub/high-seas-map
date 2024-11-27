import requests
import spacy
import psycopg
import os

def process_similarity():
  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT (id, readme_url) FROM ships")
      ships = cur.fetchall()

  if len(ships) == 0:
    print("Ships not downloaded.")
    return
  
  filtered_ships = {}

  nlp = spacy.load("en_core_web_md")
  normalized_list = []
  id_list = []
  print("Downloading & normalizing ship READMEs...")
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
            
          value = normalized_list[x].similarity(normalized_list[y])
          insertArgs.append((id_list[x], id_list[y], max(0, value)))
    
      updateArgs = []
      for ship in filtered_ships:
        updateArgs.append((ship,))
        
      cur.executemany("INSERT INTO similarity (shipa, shipb, value) VALUES (%s, %s, %s)", insertArgs)
      cur.executemany("UPDATE ships SET filtered = true WHERE id = %s", updateArgs)
    
    conn.commit()

  print("Done with similarity")