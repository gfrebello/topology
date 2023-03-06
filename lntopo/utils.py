import requests
import os
import sys
import csv
import json
import click
import networkx as nx
from tqdm import tqdm 
import random 

def confirm():
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("Continue [Y/N]? ").lower()
    return answer == "y"

@click.group()
def utils():
    pass

@utils.command()
@click.option('--fmt', type=click.Choice(['dot', 'gml', 'graphml', 'json'], case_sensitive=False))
@click.argument('input_graph', type=str, required=True)
@click.argument('output_location', type=str, required=True)
def build_capacities(input_graph, output_location, fmt='gml'):
    if os.path.exists(output_location) and os.stat(output_location).st_size > 0:
        print("WARNING: overwriting file", output_location)
        if not confirm():
            print("Aborting...")
            sys.exit(0)

    if fmt == 'dot':
        g = nx.drawing.nx_pydot.read_dot(input_graph)

    elif fmt == 'gml':
        g = nx.readwrite.read_gml(input_graph)

    elif fmt == 'graphml':
        g = nx.readwrite.read_graphml(input_graph)

    elif fmt == 'json':
        with(input_graph,'r') as f:
            json_graph = json.load(f)
        g = nx.readwrite.node_link_data(json_graph)
        
    with open(output_location, 'w+') as f:
        queried = []
        writer = csv.writer(f)
        writer.writerow(['scid','capacity_sat'])
        for u, v, attr in tqdm(g.edges(data=True), desc=' '.join(["Bulding capacities file at", output_location])):
            undirected_scid = attr['scid'][:-2]
            if undirected_scid not in queried:
                scid_elements = [ int(i) for i in undirected_scid.split("x") ]
                converted_scid = scid_elements[0] << 40 | scid_elements[1] << 16 | scid_elements[2]
                url = "https://1ml.com/channel/" + str(converted_scid) + "/json"
                resp = requests.get(url)
                if resp.status_code == 200:
                    channel_info = resp.json()
                else:
                    raise Exception("ERROR: unable to retrieve channel.")
                writer.writerow([undirected_scid, channel_info['capacity']])
                queried.append(undirected_scid)

