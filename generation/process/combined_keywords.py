import requests
import click
from os.path import exists
import json
from pickle import load
import os
import spacy

def process_combined_keywords():
  if not exists("data/model.pkl"):
    click.echo("Model not trained. Please run `python main.py process model` first.")
    return
  if not exists("data/vectorizer.pkl"):
    click.echo("Vectorizer not trained. Please run `python main.py process model` first.")
    return
  with open("data/model.pkl", "rb") as f:
    clf = load(f)
  with open("data/vectorizer.pkl", "rb") as f:
    vectorizer = load(f)

  def predict_category(text):
    """
    Predict the category of a given text using the trained classifier.
    """
    text_vec = vectorizer.transform([text])
    prediction = clf.predict(text_vec)
    return prediction

  # Example usage
#   sample_text = """
# # trivia-study-site
# study site for trivia, multiple choice and free answer question types

# """
#   predicted_category = predict_category(sample_text)
#   print(f'The predicted category is: {predicted_category}')

  if not exists("data/ships.json"):
    click.echo("Ships not downloaded. Please run `python main.py download ships` first.")
    return

  shipsFile = open('data/ships.json', 'r', encoding='utf-8')
  ships = json.loads(shipsFile.read())

  nlp = spacy.load("en_core_web_lg")
  # Use in local dev
  # nlp = spacy.load("en_core_web_sm")

  keywords = {}
  filtered_ships = {}

  with click.progressbar(ships, label="Generating keywords...") as bar:
    for ship in bar:
      try:
        readme_text = requests.get(ship["fields"]["readme_url"])
      except:
        click.echo(f"Skipping ship record {ship['id']} as it does not have a valid README")
        continue

      if readme_text.status_code != 200:
        click.echo(f"Skipping ship record {ship['id']} as it does not have a valid README")
        continue

      tags = list(filter(lambda t: t != "", predict_category(readme_text.text)[0]))

      doc = nlp(readme_text.text)

      doc_tags = list(map(lambda e: e.text, doc.ents))

      tags.extend(doc_tags)

      if len(tags) == 0:
        click.echo(f"Skipping ship record {ship['id']} since it does not have any tags")
        continue

      keywords[ship['id']] = tags
      filtered_ships[ship['id']] = ship

  keywords_json = json.dumps(keywords)
  keywords_file = open('data/keywords.json', 'w', encoding='utf-8')
  keywords_file.write(keywords_json)

  if not os.path.exists("../frontend/public/data"):
    os.mkdir("../frontend/public/data")

  ships_json = json.dumps(filtered_ships)
  ships_file = open('../frontend/public/data/filtered_ships.json', 'w', encoding='utf-8')
  ships_file.write(ships_json)
