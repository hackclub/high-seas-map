import igraph as ig
import os
from math import floor, sqrt, ceil
import numpy as np
import psycopg
from joblib import Parallel, delayed
from random import random

def find_ship_name(ships, shipId):
  for ship in ships:
    if ship["id"] == shipId:
      return ship["name"]

def process_graph():
  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT (shipa, shipb, nlp_value, lang_value) FROM similarity")
      data = cur.fetchall()

    with conn.cursor() as cur:
      cur.execute("SELECT id FROM ships WHERE filtered = true")
      filtered_ships = list(filter(lambda r: r[0] != "HIGH_SEAS_ISLAND", cur.fetchall()))

  if len(data) == 0:
    print("Similarities not processed.")
    return

  print("Building graph...")
  def process_lang_index(row):
    shipA = row[0][0]
    shipB = row[0][1]
    value = float(row[0][3])

    return ((shipA, shipB), float(value))
  
  edges_result = Parallel(n_jobs=4)(delayed(process_lang_index)(row) for row in data)
  filtered_ships = list(map(lambda row: row[0], filtered_ships))
  g = ig.Graph()
  g.add_vertices(filtered_ships)
  edges, weights = list(zip(*filter(lambda r: r != None, edges_result)))
  g.add_edges(edges, {
    'weight': weights
  })

  print("Clustering...")
  clustering = g.community_leiden(weights="weight", n_iterations=10, resolution=0.01)
  print(clustering.modularity)
  print(clustering.summary())

  def process_nlp_index(row, allowed_list):
    shipA = row[0][0]
    shipB = row[0][1]

    if (shipA not in allowed_list) or (shipB not in allowed_list):
      return None

    value = float(row[0][2])

    if float(value) < 0.5:
      return None
    else:
      return ((shipA, shipB), float(value))

  cluster_count = max(clustering.membership) + 1
  clusters_layouts = []

  with Parallel(n_jobs=4) as parallel:
    for cluster_idx in range(0, cluster_count):
      cluster_node_ids = []
      cluster_ships = []
      for (node_id, cluster) in enumerate(clustering.membership):
        if cluster == cluster_idx:
          cluster_node_ids.append(node_id)
          cluster_ships.append(g.vs[node_id]["name"])
      
      if len(cluster_ships) == 1:
        single_layout = {}
        single_layout[cluster_ships[0]] = [random(), random()]
        clusters_layouts.append(single_layout)
      else:
        sg = ig.Graph()
        edges_result = parallel(delayed(process_nlp_index)(row, cluster_ships) for row in data)
        sg.add_vertices(cluster_ships)
        edges, weights = list(zip(*filter(lambda r: r != None, edges_result)))
        sg.add_edges(edges, {
          'weight': weights
        })

        min_coords = []
        max_coords = []
        for v in sg.vs:
          min_coords.append(0)
          max_coords.append(1)

        sg_layout = sg.layout("fr", weights="weight", minx=min_coords, miny=min_coords, maxx=max_coords, maxy=max_coords)

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

        SCALE_RES = 50
        scaled_nodes = {}
        for nodeId in nodes.keys():
          node = nodes[nodeId]

          percent_x = (node[0] - min_x) / (max_x - min_x)
          scaled_x = aspect * SCALE_RES * percent_x

          percent_y = (node[1] - min_y) / (max_y - min_y)
          scaled_y = (1 / aspect) * SCALE_RES * percent_y

          scaled_nodes[nodeId] = [scaled_x, scaled_y]

        clusters_layouts.append(scaled_nodes)

    

  print("Plotting graph...")

  min_coords = []
  max_coords = []
  
  # np.random.seed(4)
  cg = clustering.cluster_graph(combine_vertices="first")
  for v in cg.vs:
    min_coords.append(0)
    max_coords.append(1)
  
  island_found = False
  while not island_found:
    seed = np.random.rand(len(cg.vs), 2)

    layout = cg.layout("kk", seed=seed, minx=min_coords, miny=min_coords, maxx=max_coords, maxy=max_coords)

    nodes = {}
    for i, coord in enumerate(layout._coords): 
      key = cg.vs[i]['name']

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

    SCALE_RES = 400
    scaled_clusters = {}
    for nodeId in nodes.keys():
      node = nodes[nodeId]

      percent_x = (node[0] - min_x) / (max_x - min_x)
      scaled_x = aspect * SCALE_RES * percent_x

      percent_y = (node[1] - min_y) / (max_y - min_y)
      scaled_y = (1 / aspect) * SCALE_RES * percent_y

      scaled_clusters[nodeId] = [scaled_x, scaled_y]

    # island placing
    print("Placing central island...")
    
    grid = []
    for y in range(0, SCALE_RES, 1):
      row = []

      for x in range(0, SCALE_RES, 1):
        row.append(False)

        for id in scaled_clusters.keys():
          n = scaled_clusters[id]

          if floor(n[0]) == x and floor(n[1]) == y:
            row[x] = True
            break;
      
      grid.append(row)
    
    island_width = ceil(SCALE_RES * 0.01)
    island_height = ceil(SCALE_RES * 0.01)

    x_streak = 0
    islandLocations = []
    for y in range(floor(len(grid) / 4), floor(3 * (len(grid) - island_height) / 4)):
      for x in range(floor(len(grid[y]) / 4), floor(3 * (len(grid[y]) - island_width) / 4)):
        if grid[y][x]:
          x_streak += 1
        
        if x_streak == island_width:
          bad = False

          for checkY in range(y+1, y + island_height + 1):
            for checkX in range(x, x + island_width + 1):
              if grid[checkY][checkX]:
                bad = True
                x_streak = 0
                break

            if bad:
              break
          
          if not bad:
            islandLocations.append([x - island_width + (island_width / 2), y + (island_height / 2)])

    if len(islandLocations) == 0:
      print("No island location found for graph, regenerating...\n")
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

  final_nodes = {}
  final_nodes["HIGH_SEAS_ISLAND"] = closest_location

  print("Pasting in subgraphs...")
  for (idx, cluster) in enumerate(clusters_layouts):
    cluster_name = cg.vs[idx]["name"]
    cluster_x = scaled_clusters[cluster_name][0]
    cluster_y = scaled_clusters[cluster_name][1]

    print(cluster)

    for cluster_node in cluster:
      final_nodes[cluster_node] = [cluster[cluster_node][0] + cluster_x, cluster[cluster_node][1] + cluster_y]

  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      args = []
      for node in final_nodes:
        args.append((final_nodes[node][0], final_nodes[node][1], node))
      
      cur.executemany("UPDATE ships SET x_pos = %s, y_pos = %s WHERE id = %s", args)

    conn.commit()

  print("Done with graph")
