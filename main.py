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
    duration = 3600  # seconds

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

    miners = {
        'Ohio': {
            'how_many': 5,
            'mega_hashrate_range': "(20, 40)"
        },
        'Tokyo': {
            'how_many': 2,
            'mega_hashrate_range': "(20, 40)"
        },
        'Ireland': {
            'how_many': 2,
            'mega_hashrate_range': "(20, 40)"
        },
    }
    non_miners = {
        'Ohio': {
            'how_many': 50,
        },
        'Tokyo': {
            'how_many': 50,
        },
        'Ireland': {
            'how_many': 50,
        },
    }

    node_factory = NodeFactory(world, network)
    # Create all nodes
    nodes_list = node_factory.create_nodes(miners, non_miners)
    # Start the network heartbeat
    world.env.process(network.start_heartbeat())

    # Connect each to at least k peers
    k=4
    G = nx.connected_watts_strogatz_graph(len(nodes_list), 4, .3)
    for u in G:
        nodes_list[u].connect(nodes_list[v] for v in G[u])

    transaction_factory = TransactionFactory(world)
    transaction_factory.broadcast(100, 400, 15, nodes_list)

    world.start_simulation()

    report_node_chain(world, nodes_list)
    write_report(world)
    return world, nodes_list


if __name__ == '__main__':
    run_model()
