import json
from os.path import exists
import requests
from sentence_transformers import SentenceTransformer

def process_similarity():
  if not exists("data/ships.json"):
    print("Ships not downloaded. Please run `python main.py download ships` first.")
    return

  shipsFile = open('data/ships.json', 'r', encoding='utf-8')
  ships = json.loads(shipsFile.read())

  indices = {}
  filtered_ships = {}

  model = SentenceTransformer("all-mpnet-base-v2", similarity_fn_name="dot")

  normalized_list = []
  id_list = []
  print("Downloading & normalizing ship READMEs...")
  for ship in ships:
    try:
      readme_text = requests.get(ship["fields"]["readme_url"])
    except:
      print(f"Skipping ship record {ship['id']} as it does not have a valid README")
      continue

    if readme_text.status_code != 200:
      print(f"Skipping ship record {ship['id']} as it does not have a valid README")
      continue

    normalized = readme_text.text[0:5000]
    embedding = model.encode(normalized)

    normalized_list.append(embedding)
    id_list.append(ship['id'])
    filtered_ships[ship['id']] = ship

  print("Calculating similarity...")
  matrix = model.similarity(normalized_list, normalized_list)

  print("Building similarity pairs...")
  indices = {}
  for x in range(len(matrix)):
    for y in range(len(matrix[x])):
      if x == y:
        continue
      value = matrix[x][y].item()
      indices[f"{id_list[x]}-{id_list[y]}"] = max(0, value)

  similarityIndicesFile = open('data/similarity_indices.json', 'w', encoding='utf-8')
  similarityIndicesFile.write(json.dumps(indices))

  ships_json = json.dumps(filtered_ships)
  ships_file = open('data/filtered_ships.json', 'w', encoding='utf-8')
  ships_file.write(ships_json)