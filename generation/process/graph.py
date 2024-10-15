import json
import click
import igraph as ig
from os.path import exists
import re
from math import sqrt

def find_ship_name(ships, shipId):
  for ship in ships:
    if ship["id"] == shipId:
      return ship["name"]

def process_graph():
  g = ig.Graph()

  if not exists("data/similarity_indices.json"):
    click.echo("Similarities not processed. Please run `python main.py process similarity` first.")
    return

  file = open("data/similarity_indices.json", "r", encoding="utf-8")
  data = dict(json.load(file))

  edges = []

  with click.progressbar(list(data.items()), label="Building graph...") as bar:
    for (key, value) in bar:
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

  click.echo("Plotting graph...")

  clustered = g.community_leiden(weights=g.es["weight"], resolution=5, n_iterations=20)
  # layout = g.layout("fr", niter=2000, start_temp=(sqrt(len(g.vs)) / 5))
  layout = g.layout("graphopt", node_charge=0.025, node_mass=10, spring_length=2, niter=300)

  cplot = ig.plot(clustered, None, layout=layout, bbox=(10, 10))
  objstr = re.split(r'\[\s*\d\] ', str(cplot._objects[0][0]))
  objstr.pop(0)

  def map_ship(ship: str):
    ids = ship.strip().split(',')
    ids = map(lambda id: id.strip(), ids)

    return ids

  clusters = map(map_ship, objstr)
  objects = []
  pretty_clusters = []
  for cluster in clusters:
    pretty_cluster = []
    for obj in cluster:
      for n in obj.split('\n'):
        node_id = re.split(r'\[.+\] ', n)[-1]
        objects.append(node_id)
        pretty_cluster.append(node_id)
    pretty_clusters.append(pretty_cluster)

  nodes = {}
  for i in range(len(objects)):
    key = objects[i]
    nodes[key] = cplot._objects[0][5]['layout'].__dict__['_coords'][i]

  nodes_json = json.dumps(nodes)
  nodes_file = open('../frontend/public/data/nodes.json', 'w', encoding='utf-8')
  nodes_file.write(nodes_json)

  clusters_json = json.dumps(pretty_clusters)
  clusters_file = open('data/clusters.json', 'w', encoding='utf-8')
  clusters_file.write(clusters_json)
