import os
from pyairtable import Api
from dotenv import load_dotenv
import requests
import spacy
import igraph
import re
import json

load_dotenv()

api = Api(os.environ['AIRTABLE_API_KEY'])
ships_table = api.table(os.environ['AIRTABLE_BASE'], os.environ['AIRTABLE_TABLE'])

# all_ships = ships_table.all(formula="{hidden} = FALSE()")
all_ships = ships_table.all()

nlp = spacy.load("en_core_web_lg")

keywords = {}
filtered_ships = {}

print("Processing keywords for ships...")
for ship in all_ships:
  readme_url = ship.get("fields").get("readme_url")
  if readme_url == None:
    print(f"Skipping ship record {ship['id']} since it does not have a README URL")
    continue

  readme_text = requests.get(readme_url)

  doc = nlp(readme_text.text)

  if len(doc.ents) == 0:
    print(f"Skipping ship record {ship['id']} since it does not have any keywords")
    continue

  keywords[ship['id']] = list(map(lambda e: e.text, doc.ents))
  filtered_ships[ship['id']] = ship

ships_json = json.dumps(filtered_ships)
ships_file = open('frontend/public/data/filtered_ships.json', 'w', encoding='utf-8')
ships_file.write(ships_json)

indices = {}

print("Processing ship similarities...")
for shipA in keywords:
  for shipB in keywords:
    if shipA == shipB:
      continue

    intersection = set(keywords[shipA]).intersection(set(keywords[shipB]))
    union = set(keywords[shipA]).union(set(keywords[shipB]))

    jaccard = len(intersection) / len(union)

    indices[shipA + "-" + shipB] = jaccard

g = igraph.Graph()
edges = []

print("Building ship graph...")
for (key, value) in indices.items():
  if float(value) < 0.2:
    continue

  shipA = str(key).split('-')[0]
  shipB = str(key).split('-')[1]

  try:
    g.vs.find(name=shipA)
  except:
    g.add_vertex(shipA)

  try:
    g.vs.find(name=shipB)
  except:
    g.add_vertex(shipB)
  
  g.add_edge(shipA, shipB, weight=float(value))
  edges.append(f'{shipA}-{shipB}')

print("Plotting graph...")
clustered = g.community_leiden(weights=g.es["weight"], resolution=5, n_iterations=20)
layout = g.layout("kk")

cplot = igraph.plot(clustered, None, layout=layout, bbox=(10, 10))
objstr = re.split(r'\[\s*\d\] ', str(cplot._objects[0][0]))
objstr.pop(0)

def map_ship(ship: str):
  ids = ship.strip().split(',')
  ids = map(lambda id: id.strip(), ids)

  return ids

clusters = map(map_ship, objstr)
objects = []
for cluster in clusters:
  for obj in cluster:
    for n in obj.split('\n'):
      objects.append(re.split(r'\[.+\] ', n)[-1])

nodes = {}
for i in range(len(objects)):
  key = objects[i]
  nodes[key] = cplot._objects[0][5]['layout'].__dict__['_coords'][i]

nodes_json = json.dumps(nodes)
nodes_file = open('frontend/public/data/nodes.json', 'w', encoding='utf-8')
nodes_file.write(nodes_json)

edges_json = json.dumps(edges)
edges_file = open('frontend/public/data/edges.json', 'w', encoding='utf-8')
edges_file.write(edges_json)
