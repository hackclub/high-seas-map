import click
from dotenv import load_dotenv

from download.ships import download_ships
from process.similarity import process_similarity
from process.keywords import process_keywords
from process.graph import process_graph
from all import run_all

load_dotenv()

@click.group()
def root():
	pass

@root.command()
def all():
	run_all()

@root.group()
def download():
	pass

@download.command()
def ships():
	download_ships()
	
@root.group()
def process():
	pass

@process.command()
def similarity():
	process_similarity()

@process.command()
def keywords():
	process_keywords()
	
@process.command()
def graph():
	process_graph()

@root.group()
def query():
	pass

if __name__ == '__main__':
	root()


