from download.ships import download_ships
from process.similarity import process_similarity
from process.graph import process_graph
import psycopg
import os
import gc
import psutil

def run_all():
  process = psutil.Process()

  ships = download_ships(reset=False)
  print(process.memory_info().rss)
  gc.collect()
  
  similarity, filtered = process_similarity(ships)
  print(process.memory_info().rss)
  gc.collect()

  nodes = process_graph(similarity, filtered)
  print(process.memory_info().rss)
  gc.collect()

  with psycopg.connect(os.environ["DB_URI"]) as conn:
    with conn.cursor() as cur:
      cur.execute("DELETE FROM similarity")
      cur.execute("DELETE FROM ships")

      args = []
      for ship in ships:
        if ship["id"] not in filtered:
          continue

        x_pos = nodes[ship["id"]][0]
        y_pos = nodes[ship["id"]][1]
        args.append((ship["id"], ship["fields"]["identifier"], ship["fields"]["readme_url"], ship["fields"]["repo_url"],
                          ship["fields"]["title"], ship["fields"]["screenshot_url"], ship["fields"]["hours"],
                          ship["fields"]["entrant__slack_id"][0], ship["fields"]["slack_username"], x_pos, y_pos))
      
      cur.execute("INSERT INTO ships (id, filtered, x_pos, y_pos) VALUES ('HIGH_SEAS_ISLAND', true, %s, %s)", (nodes["HIGH_SEAS_ISLAND"][0], nodes["HIGH_SEAS_ISLAND"][1]))
      cur.executemany("""
                    INSERT INTO ships (id, ship_id, readme_url, repo_url, title, screenshot_url, hours, slack_id, slack_username, filtered, x_pos, y_pos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true, %s, %s)
                    """, args)
      
      cur.executemany("INSERT INTO similarity (shipa, shipb, top_lang_value, lang_value) VALUES (%s, %s, %s, %s)", similarity)

      cur.close()
    
    conn.commit()
    conn.close()
  
  print("Done with all")
