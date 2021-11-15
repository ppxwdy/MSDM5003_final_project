from multiprocessing import Process, Manager
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd
import copy


def generator2(N, m, ks):
    """
    generate the network
    :param N: number of nodes
    :param m: new node has m links
    :return:
    """

    # generate a BA network with 4000 nodes and <k> = 2m = 4
    ba = nx.barabasi_albert_graph(N, m, seed=666)

    # nodes
    nodes = [i for i in range(N)]

    # get the neighbours for each vert [(0, [1, 2]), (1, [0, 3]), (2, [0, 3]), (3, [1, 2])]
    adj = [(n, list(nbrdict.keys())) for n, nbrdict in ba.adjacency()]
    # get the degrees [(0, [1, 2]), (1, [0, 3]), (2, [0, 3]), (3, [1, 2])]
    degrees = list(ba.degree())

    identity = np.ones(N, dtype=int)
    # based on the k threshold to asign C or D
    # k >= k* will be C, otherwise will be D
    for node in range(N):
        d = degrees[node][1]
        if d > ks:
            identity[node] = 0

    return ba, adj, identity, degrees, nodes


def cal_gain(node, b, adj, identity):
    """
    calculate gain for the given node
    :param node: the node i
    """
    neighbours = adj[node][1]
    gain = 0
    idi = identity[node]
    for n in neighbours:
        idj = identity[n]
        if idi == idj and idi == 0:
            gain += 1
        elif idi == 1 and idj == 0:
            gain += b
    return gain


def update2(nodei, nodej, b, gains, identity, degrees):
    """
    compare nodei's gain with its neighbour nodej, and find out
    how to udpate nodei's od
    :param nodei: nodei
    :param nodej: nodej
    :return:
    """

    if gains[nodei] < gains[nodej]:
        beta = 1 / (max(degrees[nodei][1], degrees[nodei][1]) * b)
        dice = np.random.rand()
        # dice <= beta means accept
        if dice <= beta:
            identity[nodei] = identity[nodej]


def choose_neighbor(nodei, adj):
    """
    choose the node j for the node compare the gain
    :param nodei: the node we need to find a neighbour for
    :return: the neighbour chosen randomly
    """
    neighbors = adj[nodei][1]
    dice = np.random.randint(0, len(neighbors))
    return neighbors[dice]


# generate the b values
bs = np.arange(1, 3.3, 0.1)

# transient time
t0 = 50
# get steady
t1 = 10
# after steady
ts = 10000

N = 4000
m = 2


# def iter(N, m, b, k, record):
#     ct = []
#     sb = time.time()
#     # generate the graph
#     ba, adj, identity, degrees, nodes = generator2(N, m, k)
#
#     # pre-evo
#     for t in range(t0):
#         # calculate gain
#         gains = dict()
#         for node in nodes:
#             gains[node] = cal_gain(node, b, adj, identity)
#         # update
#         for node in nodes:
#             nodej = choose_neighbor(node, adj)
#             update2(node, nodej, b, gains, identity, degrees)
#         ct.append((N - np.sum(identity)) / N)
#
#     # get steady
#     key = True
#     for t in range(t1):
#         oldc = N - np.sum(identity)
#         # calculate gain
#         gains = dict()
#         for node in nodes:
#             gains[node] = cal_gain(node, b, adj, identity)
#         # update
#         for node in nodes:
#             nodej = choose_neighbor(node, adj)
#             update2(node, nodej, b, gains, identity, degrees)
#         newc = N - np.sum(identity)
#         # find out reach steady state or not
#         if key:
#             if abs(newc - oldc) < 1 / np.sqrt(N):
#                 print(f'we have reached the steady state after {t} times evolution.')
#                 key = False
#         ct.append((N - np.sum(identity)) / N)
#     eb = time.time()
#
#     print(f'The time we used for b = {b} is {eb - sb}s.')
#     record[b] = ct


def iter(adj, identity, degrees, nodes, b, record, start):
    ct = [start]
    sb = time.time()
    # generate the graph
    # ba, adj, identity, degrees, nodes = generator2(N, m, k)

    # pre-evo
    for t in range(t0):
        # calculate gain
        gains = dict()
        for node in nodes:
            gains[node] = cal_gain(node, b, adj, identity)
        # update
        for node in nodes:
            nodej = choose_neighbor(node, adj)
            update2(node, nodej, b, gains, identity, degrees)
        ct.append((N - np.sum(identity)) / N)

    # get steady
    key = True
    for t in range(t1):
        oldc = N - np.sum(identity)
        # calculate gain
        gains = dict()
        for node in nodes:
            gains[node] = cal_gain(node, b, adj, identity)
        # update
        for node in nodes:
            nodej = choose_neighbor(node, adj)
            update2(node, nodej, b, gains, identity, degrees)
        newc = N - np.sum(identity)
        # find out reach steady state or not
        if key:
            if abs(newc - oldc) < 1 / np.sqrt(N):
                print(f'we have reached the steady state after {t} times evolution.')
                key = False
        ct.append((N - np.sum(identity)) / N)
    eb = time.time()

    print(f'The time we used for b = {b} is {eb - sb}s.')
    record[b] = ct


def takefirst(x):
    return x[0]


if __name__ == '__main__':
    ma = Manager()

    record1 = ma.dict()
    record2 = ma.dict()
    s = time.time()
    processes = []
    k1 = 2
    k2 = 3
    ba, adj, identity, degrees, nodes = generator2(N, m, k1)
    start = float("%.4f" % ((N - np.sum(identity)) / N))
    for i in range(0, 24, 8):
        bs_ = bs[i:i + 8]
        for b in bs:
            adj_ = copy.deepcopy(adj)
            id_ = copy.deepcopy(identity)
            de_ = copy.deepcopy(degrees)
            nodes_ = copy.deepcopy(nodes)

            p = Process(target=iter, args=(adj_, id_, de_, nodes_, b, record1, start))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

    ba, adj, identity, degrees, nodes = generator2(N, m, k2)
    start = float("%.4f" % ((N - np.sum(identity)) / N))
    for i in range(0, 24, 8):
        bs_ = bs[i:i + 8]
        for b in bs:
            adj_ = copy.deepcopy(adj)
            id_ = copy.deepcopy(identity)
            de_ = copy.deepcopy(degrees)
            nodes_ = copy.deepcopy(nodes)
            p = Process(target=iter, args=(adj_, id_, de_, nodes_, b, record2, start))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()
    print(f'The whole process include t0 and t1 need {time.time() - s}s')

    # save the data
    # data = pd.DataFrame({'<c>': c_means_, 'PC': pcs_, 'PD': pds_, 'F': fs_})
    # data.to_csv('part1 data.csv', index=False, sep=',')
    t = [i for i in range(1, t0 + t1 + 2)]
    fig, ax = plt.subplots(2, 1, figsize=(10, 20), sharex='all')
    for b in bs:
        ax[0].plot(t, record1[b], 'o-', label='b = ' + str(b))
        ax[1].plot(t, record2[b], 's-', label='b = ' + str(b))
        print(record1[b][0], '1111')
        print(record2[b][0], '2222')
    plt.xlabel('t')
    plt.xscale('log')

    ax[0].set_yscale('log')
    ax[1].set_yscale('log')
    ax[0].legend()
    ax[1].legend()

    # plt.savefig('pic1.png')
    plt.show()
