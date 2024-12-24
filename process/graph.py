import igraph as ig
import os
from math import floor, sqrt, ceil
import numpy as np
import psycopg
from joblib import Parallel, delayed
from random import random
import gc

def find_ship_name(ships, shipId):
  for ship in ships:
    if ship["id"] == shipId:
      return ship["name"]
    
def process_top_lang_index(row):
  shipA = row[0][0]
  shipB = row[0][1]
  value = float(row[0][2])

  return ((shipA, shipB), float(value))

def process_lang_index(row, allowed_list):
  shipA = row[0][0]
  shipB = row[0][1]
  value = float(row[0][3])

  if (shipA not in allowed_list) or (shipB not in allowed_list) or value == 0:
    return None

  return ((shipA, shipB), float(value))

def process_cluster_edges(i, count, cluster_length):
  edges= []
  for j in range(cluster_length):
    if count != 0:
      edges.append(((i, j), 1 / count / 5))
  
  return edges

def process_subgraph(g, data, cluster_idx, membership):
  cluster_node_ids = []
  cluster_ships = []
  for (node_id, cluster) in enumerate(membership):
    if cluster == cluster_idx:
      cluster_node_ids.append(node_id)
      cluster_ships.append(g.vs[node_id]["name"])
  
  SIZE_FACTOR = len(cluster_ships) / 5
  SCALE_RES = SIZE_FACTOR * 200
  if len(cluster_ships) == 1:
    single_layout = {}
    single_layout[cluster_ships[0]] = [random() * SCALE_RES, random() * SCALE_RES]
    return single_layout
  else:
    sg = ig.Graph()

    edges_result = Parallel(n_jobs=4)(delayed(process_lang_index)(row, cluster_ships) for row in data)
    sg.add_vertices(cluster_ships)
    filtered_result = list(filter(lambda r: r != None, edges_result))
    if len(filtered_result) == 0:
      random_layout = {}
      for ship in cluster_ships:
        random_layout[ship] = [random() * SCALE_RES, random() * SCALE_RES]
      return random_layout
    
    edges, weights = list(zip(*filtered_result))
    sg.add_edges(edges, {
      'weight': weights
    })

    min_coords = []
    max_coords = []
    for v in sg.vs:
      min_coords.append(0)
      max_coords.append(SIZE_FACTOR)

    sg_layout = sg.layout("kk", weights="weight", minx=min_coords, miny=min_coords, maxx=max_coords, maxy=max_coords)

    nodes = {}
    for i, coord in enumerate(sg_layout._coords): 
      key = sg.vs[i]['name']

      nodes[key] = coord

    min_x = 0
    max_x = 0
    min_y = 0
    max_y = 0
    for key in nodes:
      coords = nodes[key]
      if coords[0] < min_x:
        min_x = coords[0]
      if coords[0] > max_x:
        max_x = coords[0]
      if coords[1] < min_y:
        min_y = coords[1]
      if coords[1] > max_y:
        max_y = coords[1]

    aspect = (max_x - min_x) / (max_y - min_y)

    scaled_nodes = {}
    for nodeId in nodes.keys():
      node = nodes[nodeId]

      percent_x = (node[0] - min_x) / (max_x - min_x)
      scaled_x = aspect * SCALE_RES * percent_x

      percent_y = (node[1] - min_y) / (max_y - min_y)
      scaled_y = (1 / aspect) * SCALE_RES * percent_y

      scaled_nodes[nodeId] = [scaled_x, scaled_y]

    return scaled_nodes

def process_graph(similarity, pre_ships):
  if similarity != None:
    data = list(map(lambda s: [s], similarity))
    filtered_ships = list(map(lambda s: [s], pre_ships))
  else:
    with psycopg.connect(os.environ["DB_URI"]) as conn:
      with conn.cursor() as cur:
        cur.execute("SELECT (shipa, shipb, top_lang_value, lang_value) FROM similarity")
        data = cur.fetchall()

      with conn.cursor() as cur:
        cur.execute("SELECT id FROM ships WHERE filtered = true")
        filtered_ships = list(filter(lambda r: r[0] != "HIGH_SEAS_ISLAND", cur.fetchall()))

  if len(data) == 0:
    print("Similarities not processed.")
    return

  island_found = False
  while not island_found:
    print("Building graph...")
    
    edges_result = Parallel(n_jobs=4)(delayed(process_top_lang_index)(row) for row in data)
    filtered_ships = list(map(lambda row: row[0], filtered_ships))
    g = ig.Graph()
    g.add_vertices(filtered_ships)
    g.add_vertex("HIGH_SEAS_ISLAND")
    edges, weights = list(zip(*filter(lambda r: r != None, edges_result)))
    g.add_edges(edges, {
      'weight': weights
    })

    print("Clustering...")
    clustering = g.community_leiden(weights="weight", n_iterations=50, resolution=0.5)
    print(clustering.modularity)
    print(clustering.summary())

    cluster_count = max(clustering.membership) + 1
      
    def subgraphs():
      for cluster_idx in range(0, cluster_count):
        gc.collect()
        yield process_subgraph(g, data, cluster_idx, clustering.membership)

    print("Plotting graph...")

    min_coords = []
    max_coords = []
    
    # np.random.seed(4)
    cg = clustering.cluster_graph(combine_vertices="first", combine_edges=False)
    cg.delete_edges()
    for v in cg.vs:
      min_coords.append(0)
      max_coords.append(10)

    cluster_counts = [0] * len(cg.vs)
    for v in clustering.membership:
      cluster_counts[v] += 1

    cluster_edges_result = Parallel(n_jobs=4)(delayed(process_cluster_edges)(i, count, len(cg.vs)) for i, count in enumerate(cluster_counts))
    cluster_edges, cluster_weights = list(zip(*[edge for result in cluster_edges_result for edge in result]))
    cg.add_edges(cluster_edges, {
      'weight': cluster_weights
    })

    seed = np.random.rand(len(cg.vs), 2)
    layout = cg.layout("kk", weights="weight", seed=seed, minx=min_coords, miny=min_coords, maxx=max_coords, maxy=max_coords)
    
    # layout = cg.layout("graphopt", niter=200, node_charge=0.5, node_mass=0.1, spring_length=1)

    nodes = {}
    for i, coord in enumerate(layout._coords): 
      cluster_node = cg.vs[i]['name']

      nodes[cluster_node] = coord

    min_x = 0
    max_x = 0
    min_y = 0
    max_y = 0
    for cluster_node in nodes:
      coords = nodes[cluster_node]
      if coords[0] < min_x:
        min_x = coords[0]
      if coords[0] > max_x:
        max_x = coords[0]
      if coords[1] < min_y:
        min_y = coords[1]
      if coords[1] > max_y:
        max_y = coords[1]

      height = (max_y - min_y)
      height = 1 if height == 0 else height
      aspect = (max_x - min_x) / height

      SCALE_RES = 15000
      scaled_clusters = {}
      for nodeId in nodes.keys():
        node = nodes[nodeId]

        percent_x = (node[0] - min_x) / (max_x - min_x)
        scaled_x = aspect * SCALE_RES * percent_x

        percent_y = (node[1] - min_y) / height
        scaled_y = (1 / aspect) * SCALE_RES * percent_y

        scaled_clusters[nodeId] = [scaled_x, scaled_y]
    
    final_nodes = {}

    print("Pasting in subgraphs...")
    cluster_gen = subgraphs()
    for (idx, cluster) in enumerate(cluster_gen):
      cluster_name = cg.vs[idx]["name"]
      cluster_x = scaled_clusters[cluster_name][0]
      cluster_y = scaled_clusters[cluster_name][1]

      min_x = 0
      max_x = 0
      min_y = 0
      max_y = 0
      for cluster_node in cluster:
        coords = cluster[cluster_node]
        if coords[0] < min_x:
          min_x = coords[0]
        if coords[0] > max_x:
          max_x = coords[0]
        if coords[1] < min_y:
          min_y = coords[1]
        if coords[1] > max_y:
          max_y = coords[1]

      width = max_x - min_x
      height = max_y - min_y

      for cluster_node in cluster:
        final_nodes[cluster_node] = [cluster[cluster_node][0] + cluster_x - (width / 2), cluster[cluster_node][1] + cluster_y - (height / 2)]
    
    # island placing
    print("Placing central island...")
    
    grid = []
    GRID_FACTOR = 3
    for y in range(0, SCALE_RES, 1):
      if y % GRID_FACTOR != 0:
        grid.append([])
        continue

      row = []

      for x in range(0, SCALE_RES, 1):
        row.append(False)
        if x % GRID_FACTOR != 0:
          continue

        for id in final_nodes.keys():
          n = final_nodes[id]

          if floor(n[0]) == x and floor(n[1]) == y:
            row[x] = True
            break;
      
      grid.append(row)
    
    island_width = ceil(SCALE_RES * 0.15)
    island_height = ceil(SCALE_RES * 0.15)

    x_streak = 0
    islandLocations = []

    lowerX = (floor(len(grid) / 4) // GRID_FACTOR) * GRID_FACTOR
    for y in range(lowerX, floor(3 * (len(grid) - island_height) / 4), GRID_FACTOR):
      lowerY = (floor(len(grid[y]) / 4) // GRID_FACTOR) * GRID_FACTOR
      for x in range(lowerY, floor(3 * (len(grid[y]) - island_width) / 4), GRID_FACTOR):
        if not grid[y][x]:
          x_streak += 1
        else:
          x_streak = 0
        
        if x_streak == island_width:
          bad = False

          for checkY in range(y, y + island_height + 1, GRID_FACTOR):
            for checkX in range((x - x_streak), x + 1, GRID_FACTOR):
              if grid[checkY][checkX]:
                bad = True
                x_streak = 0
                break

            if bad:
              break
          
          if not bad:
            islandLocations.append([x - island_width + (island_width / 2), y + (island_height / 2)])

    if len(islandLocations) == 0:
      print("No island location found in graph, regenerating...\n")
      island_found = False
    else:
      island_found = True

  closest_location = [SCALE_RES, SCALE_RES]
  closest_distance = sqrt(2 * ((SCALE_RES / 2) ** 2))

  for location in islandLocations:
    distance = sqrt(((location[0] - (SCALE_RES / 2)) ** 2) + ((location[1] - (SCALE_RES / 2)) ** 2))

    if distance < closest_distance:
      closest_distance = distance
      closest_location = location

  final_nodes["HIGH_SEAS_ISLAND"] = closest_location

  print("Done with graph")

  if similarity != None:
    return final_nodes
  else:
    with psycopg.connect(os.environ["DB_URI"]) as conn:
      with conn.cursor() as cur:
        args = []
        for node in final_nodes:
          args.append((final_nodes[node][0], final_nodes[node][1], node))
        
        cur.executemany("UPDATE ships SET x_pos = %s, y_pos = %s WHERE id = %s", args)

      conn.commit()
