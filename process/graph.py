import json
import igraph as ig
import os
from math import floor, sqrt
import numpy as np
import psycopg

def process_graph():
  good_graph_found = False
  while (not good_graph_found):
    good_graph_found = gen_graph()

def find_ship_name(ships, shipId):
  for ship in ships:
    if ship["id"] == shipId:
      return ship["name"]

def gen_graph():
  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT (shipa, shipb, value) FROM similarity")
      data = cur.fetchall()

  if len(data) == 0:
    print("Similarities not processed.")
    return

  edges = []
  counted_ships = set()

  print("Building graph...")
  g = ig.Graph()
  for row in data:
    shipA = row[0][0]
    shipB = row[0][1]
    value = float(row[0][2])

    # give each ship at least one edge
    if ((shipA in counted_ships) and (shipB in counted_ships)) or value == 0:
      if float(value) < 0.4:
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
      counted_ships.add(shipA)
    if shipB not in counted_ships:
      counted_ships.add(shipB)
    
    g.add_edge(shipA, shipB, weight=float(value))
    edges.append(f'{shipA}-{shipB}')

  print("Plotting graph...")
  
  # np.random.seed(4)
  seed = np.random.rand(len(g.vs), 2)

  mincoords = []
  maxcoords = []

  for v in g.vs:
    mincoords.append(0)
    maxcoords.append(1)

  layout = g.layout("kk", weights="weight", seed=seed, minx=mincoords, miny=mincoords, maxx=maxcoords, maxy=maxcoords)

  nodes = {}
  for i, coord in enumerate(layout._coords): 
    key = g.vs[i]['name']

    nodes[key] = coord

  minX = 0
  maxX = 0
  minY = 0
  maxY = 0
  for key in nodes:
    coords = nodes[key]
    if coords[0] < minX:
      minX = coords[0]
    if coords[0] > maxX:
      maxX = coords[0]
    if coords[1] < minY:
      minY = coords[1]
    if coords[1] > maxY:
      maxY = coords[1]

  aspect = (maxX - minX) / (maxY - minY)

  scaledNodes = {}
  for nodeId in nodes.keys():
    node = nodes[nodeId]

    percentX = (node[0] - minX) / (maxX - minX)
    scaledX = aspect * 200 * percentX

    percentY = (node[1] - minY) / (maxY - minY)
    scaledY = (1 / aspect) * 200 * percentY

    scaledNodes[nodeId] = [scaledX, scaledY]

  # island placing
  print("Placing central island...")
  
  grid = []
  for y in range(0, 200, 1):
    row = []

    for x in range(0, 200, 1):
      row.append(False)

      for id in scaledNodes.keys():
        n = scaledNodes[id]

        if floor(n[0]) == x and floor(n[1]) == y:
          row[x] = True
          break;
    
    grid.append(row)
  
  islandW = 15
  islandH = 15

  xStreak = 0
  islandLocations = []
  for y in range(floor(len(grid) / 4), floor(3 * (len(grid) - islandH) / 4)):
    for x in range(floor(len(grid[y]) / 4), floor(3 * (len(grid[y]) - islandW) / 4)):
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
          islandLocations.append([x - islandW + (islandW / 2), y + (islandH / 2)])

  if len(islandLocations) == 0:
    print("No island location found for graph, regenerating...\n")
    return False
        
  closestLocation = [100, 199]
  closestDistance = sqrt(2 * (100 ** 2))

  for location in islandLocations:
    distance = sqrt(((location[0] - 100) ** 2) + ((location[1] - 100) ** 2))

    if distance < closestDistance:
      closestDistance = distance
      closestLocation = location

  scaledNodes["HIGH_SEAS_ISLAND"] = closestLocation

  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      args = []
      for node in scaledNodes:
        args.append((scaledNodes[node][0], scaledNodes[node][1], node))
      
      cur.executemany("UPDATE ships SET x_pos = %s, y_pos = %s WHERE id = %s", args)

    conn.commit()

  return True
