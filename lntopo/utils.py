import requests
import os
import csv
import json
import click
import networkx as nx
from tqdm import tqdm

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
    # if os.path.exists(output_location) and os.stat(output_location).st_size > 0:
    #     print("WARNING: overwriting file", output_location)
    #     if not confirm():
    #         print("Aborting...")
    #         sys.exit(0)

    if fmt == 'dot':
        G = nx.drawing.nx_pydot.read_dot(input_graph)

    elif fmt == 'gml':
        G = nx.readwrite.read_gml(input_graph)

    elif fmt == 'graphml':
        G = nx.readwrite.read_graphml(input_graph)

    elif fmt == 'json':
        with(input_graph,'r') as f:
            json_graph = json.load(f)
        G = nx.readwrite.node_link_data(json_graph)

    with open(output_location, 'r+') as f:
        queried = []
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            queried.append(row[0])
        writer = csv.writer(f)
        for u, v, attr in tqdm(G.edges(data=True), desc=' '.join(["Bulding capacities file at", output_location])):
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


@utils.command()
@click.option('--fmt', type=click.Choice(['dot', 'gml', 'graphml', 'json'], case_sensitive=False))
@click.argument('input_graph', type=str, required=True)
@click.argument('output_location', type=str, required=True)
@click.argument('capacities_file', type=str, required=True)
def add_capacities(input_graph, output_location, capacities_file='./data/capacities.csv', fmt='gml'):
    with open(capacities_file, 'r') as f:
        reader = csv.reader(f)
        capacities = { row[0]:row[1] for row in reader }
    
    if fmt == 'dot':
        G = nx.drawing.nx_pydot.read_dot(input_graph)

    elif fmt == 'gml':
        G = nx.readwrite.read_gml(input_graph)

    elif fmt == 'graphml':
        G = nx.readwrite.read_graphml(input_graph)

    elif fmt == 'json':
        with(input_graph,'r') as f:
            json_graph = json.load(f)
        G = nx.readwrite.node_link_data(json_graph)

    for u, v, attr in tqdm(G.edges(data=True), desc=' '.join(["Adding capacity information to", input_graph])):
        undirected_scid = attr['scid'][:-2]
        attr['capacity'] = int(capacities[undirected_scid])
    
    with open(output_location, 'w') as f:        
        if fmt == 'dot':
            print(nx.nx_pydot.to_pydot(G), file=f)

        elif fmt == 'gml':
            for line in nx.generate_gml(G):
                print(line, file=f)

        elif fmt == 'graphml':
            for line in nx.generate_graphml(G, named_key_ids=True, edge_id_from_attribute='scid'):
                print(line, file=f)

        elif fmt == 'json':
            print(json.dumps(json_graph.adjacency_data(G)), file=f)

