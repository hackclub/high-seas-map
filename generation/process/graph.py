import json
import click
import igraph as ig
from os.path import exists
import re

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
  counted_ships = set()

  g.add_vertex("HIGH_SEAS_ISLAND")
  with click.progressbar(list(data.items()), label="Building graph...") as bar:
    for (key, value) in bar:
      shipA = str(key).split('-')[0]
      shipB = str(key).split('-')[1]

      # give each ship at least one edge
      if (shipA in counted_ships) and (shipB in counted_ships):
        if float(value) < 0.05:
          continue

      try:
        g.vs.find(name=shipA)
      except:
        g.add_vertex(shipA)

      try:
        g.vs.find(name=shipB)
      except:
        g.add_vertex(shipB)

      if shipA not in counted_ships:
        g.add_edge(shipA, "HIGH_SEAS_ISLAND", weight=0.1)
      if shipB not in counted_ships:
        g.add_edge(shipB, "HIGH_SEAS_ISLAND", weight=0.1)

      counted_ships.add(shipA)
      counted_ships.add(shipB)
      
      g.add_edge(shipA, shipB, weight=float(value))
      edges.append(f'{shipA}-{shipB}')

  click.echo("Plotting graph...")

  clustered = g.community_leiden(weights=g.es["weight"], resolution=5, n_iterations=20)
  # layout = g.layout("drl")
  layout = g.layout("graphopt", node_charge=0.045, node_mass=0.5, spring_length=1, niter=200)

  cplot = ig.plot(clustered, None, layout=layout, bbox=(100, 100))
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
  minX = 0
  maxX = 0
  minY = 0
  maxY = 0
  for i in range(len(objects)):
    key = objects[i]
    coords = cplot._objects[0][5]['layout'].__dict__['_coords'][i]

    if coords[0] < minX:
      minX = coords[0]
    if coords[0] > maxX:
      maxX = coords[0]
    if coords[1] < minY:
      minY = coords[1]
    if coords[1] > maxY:
      maxY = coords[1]

    nodes[key] = coords

  nodes_json = json.dumps(nodes)
  nodes_file = open('../frontend/public/data/nodes.json', 'w', encoding='utf-8')
  nodes_file.write(nodes_json)

  clusters_json = json.dumps(pretty_clusters)
  clusters_file = open('data/clusters.json', 'w', encoding='utf-8')
  clusters_file.write(clusters_json)

  return True
