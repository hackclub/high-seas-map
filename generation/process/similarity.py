import json
from os.path import exists
import click

def process_similarity():
	if not exists("data/keywords.json"):
		click.echo("Keywords not generated. Please run `python main.py process keywords` first.")
		return

	keywordsFile = open('data/keywords.json', 'r', encoding='utf-8')
	keywords = json.loads(keywordsFile.read())

	indices = {}

	with click.progressbar(keywords, label="Generating similarity indices...") as bar:	
		for shipA in bar:
			for shipB in keywords:
				if shipA == shipB:
					continue

				intersection = set(keywords[shipA]).intersection(set(keywords[shipB]))
				union = set(keywords[shipA]).union(set(keywords[shipB]))

				jaccard = len(intersection) / len(union)

				indices[shipA + "-" + shipB] = jaccard

	similarityIndicesFile = open('data/similarity_indices.json', 'w', encoding='utf-8')
	similarityIndicesFile.write(json.dumps(indices))

	return indices