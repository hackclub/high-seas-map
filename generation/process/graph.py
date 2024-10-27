import json
import click
import igraph as ig
from os.path import exists
import re
from math import floor

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

  with click.progressbar(list(data.items()), label="Building graph...") as bar:
    for (key, value) in bar:
      shipA = str(key).split('-')[0]
      shipB = str(key).split('-')[1]

      # give each ship at least one edge
      if (shipA in counted_ships) and (shipB in counted_ships):
        if float(value) < 0.05:
          continue

      counted_ships.add(shipA)
      counted_ships.add(shipB)

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

  aspect = (maxX - minX) / (maxY - minY)
  # island placing
  click.echo("Placing central island...")

  scaledNodes = {}
  with click.progressbar(nodes.keys(), label="Scaling node coordinates...") as bar:
    for nodeId in bar:
      node = nodes[nodeId]

      percentX = (node[0] - minX) / (maxX - minX)
      scaledX = aspect * 200 * percentX

      percentY = (node[1] - minY) / (maxY - minY)
      scaledY = (1 / aspect) * 200 * percentY

      scaledNodes[nodeId] = [scaledX, scaledY]
  
  grid = []
  with click.progressbar(range(0, 200, 1), label="Building node grid...") as bar:
    for y in bar:
      row = []

      for x in range(0, 200, 1):
        row.append(False)

        for id in scaledNodes.keys():
          n = scaledNodes[id]

          if floor(n[0]) == x and floor(n[1]) == y:
            row[x] = True
            break;
      
      grid.append(row)
  
  islandW = 17
  islandH = 17

  xStreak = 0
  islandX = None
  islandY = None
  with click.progressbar(range(len(grid) - islandH), label="Finding island location...") as bar:
    for y in bar:
      for x in range(len(grid[y]) - islandW):
        if grid[y][x]:
          xStreak += 1
        
        if xStreak == islandW:
          bad = False

          for checkY in range(y+1, y + islandH + 1):
            for checkX in range(x, x + islandW + 1):
              if grid[checkY][checkX]:
                bad = True
                xStreak = 0
                break

            if bad:
              break
          
          if not bad:
            islandX = x - islandW + (islandW / 2)
            islandY = y + (islandH / 2)
        
        if islandX:
          break
      
      if islandX:
        break

  scaledNodes["HIGH_SEAS_ISLAND"] = [islandX, islandY]

  nodes_json = json.dumps(scaledNodes)
  nodes_file = open('../frontend/public/data/nodes.json', 'w', encoding='utf-8')
  nodes_file.write(nodes_json)

  clusters_json = json.dumps(pretty_clusters)
  clusters_file = open('data/clusters.json', 'w', encoding='utf-8')
  clusters_file.write(clusters_json)
