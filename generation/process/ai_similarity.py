import json
from os.path import exists
import click
import requests
from sentence_transformers import SentenceTransformer
import spacy

import os

def process_ai_similarity():
  if not exists("data/ships.json"):
    click.echo("Ships not downloaded. Please run `python main.py download ships` first.")
    return

  shipsFile = open('data/ships.json', 'r', encoding='utf-8')
  ships = json.loads(shipsFile.read())

  indices = {}
  filtered_ships = {}

  model = SentenceTransformer("all-mpnet-base-v2", similarity_fn_name="dot")
  nlp = spacy.load("en_core_web_md")

  normalized_list = []
  spacy_list = []
  id_list = []
  with click.progressbar(ships, label="Downloading & normalizing ship READMEs...") as bar:
    for ship in bar:
      try:
        readme_text = requests.get(ship["fields"]["readme_url"])
      except:
        click.echo(f"Skipping ship record {ship['id']} as it does not have a valid README")
        continue

      if readme_text.status_code != 200:
        click.echo(f"Skipping ship record {ship['id']} as it does not have a valid README")
        continue

      normalized = readme_text.text[0:5000]
      embedding = model.encode(normalized)
      spacy_embedding = nlp(normalized)

      normalized_list.append(embedding)
      spacy_list.append(spacy_embedding)
      id_list.append(ship['id'])
      filtered_ships[ship['id']] = ship

  click.echo("Calculating similarity...")
  matrix = model.similarity(normalized_list, normalized_list)

  click.echo("Building similarity pairs...")
  indices = {}
  for x in range(len(matrix)):
    for y in range(len(matrix[x])):
      if x == y:
        continue
      spacy_similarity = spacy_list[x].similarity(spacy_list[2])
      value = matrix[x][y].item()
      indices[f"{id_list[x]}-{id_list[y]}"] = (max(0, value) + max(0, spacy_similarity)) / 2

  similarityIndicesFile = open('data/similarity_indices.json', 'w', encoding='utf-8')
  similarityIndicesFile.write(json.dumps(indices))

  if not exists("../frontend/public/data"):
    os.mkdir("../frontend/public/data")

  ships_json = json.dumps(filtered_ships)
  ships_file = open('../frontend/public/data/filtered_ships.json', 'w', encoding='utf-8')
  ships_file.write(ships_json)