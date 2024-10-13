import click
from os.path import exists
import json
import openai
import os

def process_clusters():
  if not exists("../frontend/public/data/filtered_ships.json"):
    click.echo("Filtered ships not processed. Please run `python main.py process keywords` first.")
    return

  shipsFile = open('../frontend/public/data/filtered_ships.json', 'r', encoding='utf-8')
  ships = json.loads(shipsFile.read())


  if not exists("data/clusters.json"):
    click.echo("Graph not processed. Please run `python main.py process graph` first.")
    return

  file = open("data/clusters.json", "r", encoding="utf-8")
  data = list(json.load(file))

  openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url="https://jamsapi.hackclub.dev/openai/")

  named_clusters = {}
  with click.progressbar(list(data), label="Processing clusters...") as bar:
    for cluster in bar:
      titles = list(map(lambda ship_id: ships[ship_id]['fields']['title'], cluster))

      res = openai_client.chat.completions.create(
        messages=[
          {
            "role": "user",
            "content": f"Come up with a sailing/pirate-themed name for a category of projects with the following names: {", ".join(titles)}. Respond ONLY with one category name."
          }
        ],
        model="gpt-3.5-turbo"
      )

      name = res.choices[0].message.content
      named_clusters[name] = cluster
  
  named_clusters_json = json.dumps(named_clusters)
  named_clusters_file = open('../frontend/public/data/named_clusters.json', 'w', encoding='utf-8')
  named_clusters_file.write(named_clusters_json)




