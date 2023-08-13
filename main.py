import time
import os
import random

from json import dumps as dump_json

import networkx as nx

from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.transaction_factory import TransactionFactory
from blocksim.models.network import Network


def write_report(world):
    path = 'output/report.json'
    if not os.path.exists(path):
        os.mkdir('output')
        with open(path, 'w') as f:
            pass
    with open(path, 'w') as f:
        f.write(dump_json(world.env.data))


def report_node_chain(world, nodes_list):
    for node in nodes_list:
        head = node.chain.head
        chain_list = []
        num_blocks = 0
        for i in range(head.header.number):
            b = node.chain.get_block_by_number(i)
            chain_list.append(str(b.header))
            num_blocks += 1
        chain_list.append(str(head.header))
        key = f'{node.address}_chain'
        world.env.data[key] = {
            'head_block_hash': f'{head.header.hash[:8]} #{head.header.number}',
            'number_of_blocks': num_blocks,
            'chain_list': chain_list
        }


def run_model():
    now = int(time.time())  # Current time
    duration = 6*3600  # seconds

    world = SimulationWorld(
        duration,
        now,
        'input-parameters/config.json',
        'input-parameters/latency.json',
        'input-parameters/throughput-received.json',
        'input-parameters/throughput-sent.json',
        'input-parameters/delays.json')

    # Create the network
    network = Network(world.env, 'NetworkXPTO')

    locations = ['Ohio', 'Tokyo', 'Ireland']

    miners_ratios = [.1, .01, .14]
    total_nodes  = 3000

    miners = {
        location : {
            'how_many': int(total_nodes//len(locations)*miners_ratio),
            'mega_hashrate_range': "(20, 40)"
        } for location,miners_ratio in zip(locations, miners_ratios) if miners_ratio>0
    }
    non_miners = {
        location : {
            'how_many': int(total_nodes//len(locations)*(1-miners_ratio)),
        } for location,miners_ratio in zip(locations, miners_ratios)
    }

    node_factory = NodeFactory(world, network)
    # Create all nodes
    nodes_list = node_factory.create_nodes(miners, non_miners)
    # Start the network heartbeat
    world.env.process(network.start_heartbeat())

    # shuffle nodes
    # random.shuffle(nodes_list)

    # Connect each to at least k peers
    k=4
    G = nx.connected_watts_strogatz_graph(len(nodes_list), k, .25)
    for u in G:
        nodes_list[u].connect(nodes_list[v] for v in G[u])

    print('AAAAAAAAA', nx.diameter(G))

    transaction_factory = TransactionFactory(world)

    # world.start_simulation()
    epochs = 10
    for epoch in range(epochs):
        transaction_factory.broadcast(100, 300, 15, nodes_list)
        world.simulate_fraction(epoch, epochs)

    report_node_chain(world, nodes_list)
    write_report(world)
    return world, nodes_list


if __name__ == '__main__':
    run_model()
