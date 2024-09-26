import json
import spacy
import click
from os.path import exists
import os
import requests

def process_keywords():
  if not exists("data/ships.json"):
    click.echo("Ships not downloaded. Please run `python main.py download ships` first.")
    return

  shipsFile = open('data/ships.json', 'r', encoding='utf-8')
  ships = json.loads(shipsFile.read())

  nlp = spacy.load("en_core_web_lg")

  keywords = {}
  filtered_ships = {}

  with click.progressbar(ships, label="Generating keywords...") as bar:
    for ship in bar:
      readme_url = ship.get("fields").get("readme_url")

      if readme_url == None:
        click.echo(f"Skipping ship record {ship['id']} since it does not have a README URL")
        continue

      readme_text = requests.get(readme_url)

      doc = nlp(readme_text.text)

      if len(doc.ents) == 0:
        click.echo(f"Skipping ship record {ship['id']} since it does not have any keywords")
        continue

      keywords[ship['id']] = list(map(lambda e: e.text, doc.ents))
      filtered_ships[ship['id']] = ship

  keywords_json = json.dumps(keywords)
  keywords_file = open('data/keywords.json', 'w', encoding='utf-8')
  keywords_file.write(keywords_json)

  if not os.path.exists("../frontend/public/data"):
    os.mkdir("../frontend/public/data")

  ships_json = json.dumps(filtered_ships)
  ships_file = open('../frontend/public/data/filtered_ships.json', 'w', encoding='utf-8')
  ships_file.write(ships_json)