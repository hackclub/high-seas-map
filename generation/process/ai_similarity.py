import json
from os.path import exists
import click
import requests
from sentence_transformers import SentenceTransformer

import os

def process_ai_similarity():
  if not exists("data/ships.json"):
    click.echo("Ships not downloaded. Please run `python main.py download ships` first.")
    return

  shipsFile = open('data/ships.json', 'r', encoding='utf-8')
  ships = json.loads(shipsFile.read())

  indices = {}
  filtered_ships = {}

  model = SentenceTransformer("all-mpnet-base-v2")

  with click.progressbar(ships, label="Generating similarity indices...") as bar:	
    for shipA in bar:
      try:
        readme_text_a = requests.get(shipA["fields"]["readme_url"])
      except:
        click.echo(f"Skipping ship record {shipA['id']} as it does not have a valid README")
        continue

      if readme_text_a.status_code != 200:
        click.echo(f"Skipping ship record {shipA['id']} as it does not have a valid README")
        continue
    
      for shipB in ships:
        if shipA['id'] == shipB['id']:
          continue
        
        try:
          readme_text_b = requests.get(shipB["fields"]["readme_url"])
        except:
          click.echo(f"Skipping ship record {shipB['id']} as it does not have a valid README")
          continue

        if readme_text_b.status_code != 200:
          click.echo(f"Skipping ship record {shipB['id']} as it does not have a valid README")
          continue

        embeddings_a = model.encode(readme_text_a.text);
        embeddings_b = model.encode(readme_text_b.text);

        similarity = model.similarity(embeddings_a, embeddings_b);

        indices[shipA['id'] + "-" + shipB['id']] = similarity[0][0]

      filtered_ships[shipA['id']] = shipA

  similarityIndicesFile = open('data/similarity_indices.json', 'w', encoding='utf-8')
  similarityIndicesFile.write(json.dumps(indices))

  if not exists("../frontend/public/data"):
    os.mkdir("../frontend/public/data")

  ships_json = json.dumps(filtered_ships)
  ships_file = open('../frontend/public/data/filtered_ships.json', 'w', encoding='utf-8')
  ships_file.write(ships_json)