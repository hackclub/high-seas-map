import json
import click
from pyairtable import Api
import os

def download_ships():
  api = Api(os.environ['AIRTABLE_API_KEY'])
  ships_table = api.table(os.environ['AIRTABLE_BASE'], os.environ['AIRTABLE_TABLE'])

  click.echo("Downloading ships from Airtable...")
  # all_ships = ships_table.all(formula="{hidden} = FALSE()")
  all_ships = ships_table.all(fields=["identifier", "title", "readme_url", "repo_url", "screenshot_url"])

  shipsJson = json.dumps(all_ships)

  if not os.path.exists("data"):
    os.mkdir("data")
  
  file = open('data/ships.json', 'w', encoding='utf-8')
  file.write(shipsJson)

