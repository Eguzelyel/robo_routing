"""
This code is a slight modification to the code produced by Andrew Brooks,
author of the postman_problems python package.

https://networkx.github.io/documentation/stable/reference/classes/generated/networkx.Graph.add_edge.html
https://github.com/brooksandrew/postman_problems/blob/master/postman_problems/solver.py
https://github.com/brooksandrew/postman_problems/blob/master/postman_problems/graph.py
https://github.com/brooksandrew/postman_problems/blob/master/postman_problems/examples/seven_bridges/edgelist_seven_bridges.csv
"""

import warnings
import networkx as nx
import pandas as pd
import osmnx as ox
import logging
import itertools

def _get_even_or_odd_nodes(graph, mod):

    """
    Helper function for get_even_nodes.  Given a networkx object, return names of the odd or even nodes
    Args:
        graph (networkx graph): determine the degree of nodes in this graph
        mod (int): 0 for even, 1 for odd
    Returns:
        list[str]: list of node names of odd or even degree
    """

    degree_nodes = []
    for v, d in graph.degree():
        if d % 2 == mod:
            degree_nodes.append(v)
    return degree_nodes

    
def get_odd_nodes(graph):

    """
    Given a networkx object, return names of the odd degree nodes
    Args:
        graph (networkx graph): graph used to list odd degree nodes for
    Returns:
        list[str]: names of nodes with odd degree
    """

    return _get_even_or_odd_nodes(graph, 1)


def get_even_nodes(graph):

    """
    Given a networkx object, return names of the even degree nodes
    Args:
        graph (networkx graph): graph used to list even degree nodes for
    Returns:
        list[str]: names of nodes with even degree
    """

    return _get_even_or_odd_nodes(graph, 0)


def get_shortest_paths_distances(graph, pairs, edge_weight_name='distance'):

    """
    Calculate shortest distance between each pair of nodes in a graph
    Args:
        graph (networkx graph)
        pairs (list[2tuple]): List of length 2 tuples containing node pairs to calculate shortest path between
        edge_weight_name (str): edge attribute used for distance calculation
    Returns:
        dict: mapping each pair in `pairs` to the shortest path using `edge_weight_name` between them.
    """

    i = 0
    distances = {}
    for pair in pairs:
        distances[pair] = nx.dijkstra_path_length(graph, pair[0], pair[1], weight=edge_weight_name)
        if i%5 == 0:
          print(i/len(pairs))
        i+=1
    return distances


def create_complete_graph(pair_weights, flip_weights=True):
    
    """
    Create a perfectly connected graph from a list of node pairs and the distances between them.
    Args:
        pair_weights (dict): mapping between node pairs and distance calculated in `get_shortest_paths_distances`.
        flip_weights (Boolean): True negates the distance in `pair_weights`.  We negate whenever we want to find the
         minimum weight matching on a graph because networkx has only `max_weight_matching`, no `min_weight_matching`.
    Returns:
        complete (fully connected graph) networkx graph using the node pairs and distances provided in `pair_weights`
    """
    
    g = nx.Graph()
    for k, v in pair_weights.items():
        wt_i = -v if flip_weights else v
        g.add_edge(k[0], k[1], **{'distance': v, 'weight': wt_i})
    return g


def dedupe_matching(matching):

    """
    Remove duplicates node pairs from the output of networkx.algorithms.max_weight_matching since we don't care about order.
    Args:
        matching (dict): output from networkx.algorithms.max_weight_matching.  key is "from" node, value is "to" node.
    Returns:
        list[2tuples]: list of node pairs from `matching` deduped (ignoring order).
    """

    print(matching)
    matched_pairs_w_dupes = [tuple(sorted([k, v])) for k, v in matching.items()]
    return list(set(matched_pairs_w_dupes))


def add_augmenting_path_to_graph(graph, min_weight_pairs, edge_weight_name='weight'):
    
    """
    Add the min weight matching edges to the original graph
    Note the resulting graph could (and likely will) have edges that didn't exist on the original graph.  To get the
    true circuit, we must breakdown these augmented edges into the shortest path through the edges that do exist.  This
    is done with `create_eulerian_circuit`.
    Args:
        graph (networkx graph):
        min_weight_pairs (list[2tuples): output of `dedupe_matching` specifying the odd degree nodes to link together
        edge_weight_name (str): edge attribute used for distance calculation
    Returns:
        networkx graph: `graph` augmented with edges between the odd nodes specified in `min_weight_pairs`
    """
    
    graph_aug = graph.copy()  # so we don't mess with the original graph
    for pair in min_weight_pairs:
        graph_aug.add_edge(pair[0],
                           pair[1],
                           **{'distance': nx.dijkstra_path_length(graph, pair[0], pair[1], weight=edge_weight_name),
                              'augmented': True}
                           )
    return graph_aug


def create_eulerian_circuit(graph_augmented, graph_original, start_node=None):
    
    """
    networkx.eulerian_circuit only returns the order in which we hit each node.  It does not return the attributes of the
    edges needed to complete the circuit.  This is necessary for the postman problem where we need to keep track of which
    edges have been covered already when multiple edges exist between two nodes.
    We also need to annotate the edges added to make the eulerian to follow the actual shortest path trails (not
    the direct shortest path pairings between the odd nodes for which there might not be a direct trail)
    Args:
        graph_augmented (networkx graph): graph w links between odd degree nodes created from `add_augmenting_path_to_graph`.
        graph_original (networkx graph): orginal graph created from `create_networkx_graph_from_edgelist`
        start_node (str): name of starting (and ending) node for CPP solution.
    Returns:
        networkx graph (`graph_original`) augmented with edges directly between the odd nodes
    """
    
    euler_circuit = list(nx.eulerian_circuit(graph_augmented, source=start_node, keys=True))
    assert len(graph_augmented.edges()) == len(euler_circuit), 'graph and euler_circuit do not have equal number of edges.'
    
    for edge in euler_circuit:
        aug_path = nx.shortest_path(graph_original, edge[0], edge[1], weight='distance')
        edge_attr = graph_augmented[edge[0]][edge[1]][edge[2]]
        if not edge_attr.get('augmented'):
            yield edge + (edge_attr,)
        else:
            for edge_aug in list(zip(aug_path[:-1], aug_path[1:])):
                # find edge with shortest distance (if there are two parallel edges between the same nodes)
                edge_aug_dict = graph_original[edge_aug[0]][edge_aug[1]]
                edge_key = min(edge_aug_dict.keys(), key=(lambda k: edge_aug_dict[k]['distance']))  # index with min distance
                edge_aug_shortest = edge_aug_dict[edge_key]
                edge_aug_shortest['augmented'] = True
                edge_aug_shortest['id'] = edge_aug_dict[edge_key]['id']
                yield edge_aug + (edge_key, edge_aug_shortest, )


def create_required_graph(graph):

    """
    Strip a graph down to just the required nodes and edges.  Used for RPP.  Expected edge attribute "required" with
     True/False or 0/1 values.
    Args:
        graph (networkx MultiGraph):
    Returns:
        networkx MultiGraph with optional nodes and edges deleted
    """

    graph_req = graph.copy()  # preserve original structure

    # remove optional edges
    for e in list(graph_req.edges(data=True, keys=True)):
        if not e[3]['required']:
            graph_req.remove_edge(e[0], e[1], key=e[2])

    # remove any nodes left isolated after optional edges are removed (no required incident edges)
    for n in list(nx.isolates(graph_req)):
        graph_req.remove_node(n)

    return graph_req


def assert_graph_is_connected(graph):

    """
    Ensure that the graph is still a connected graph after the optional edges are removed.
    Args:
        graph (networkx MultiGraph):
    Returns:
        True if graph is connected
    """

    assert nx.algorithms.connected.is_connected(graph), "Sorry, the required graph is not a connected graph after " \
                                                        "the optional edges are removed.  This is a requirement for " \
                                                        "this implementation of the RPP here which generalizes to the " \
                                                        "CPP."
    return True


class CppGraph:
    def __init__(self, G):
    
        """
        Create a graph that can be used for the Chinese Postman
        Problem solver.
        
        Args: A graph of Chicago, G
        Return: A graph that can be run on the CPP solver
        """
        
        self.G = G
        self.g = nx.MultiGraph()
        self.start_node = None
        self.edge_count = 0
    
    def set_start(self, lat, lon):
    
        """
        Set the start/end point for the CPP.
        
        Args: Latitude and longitude
        Return: Nothing
        """
        
        self.start_node = ox.get_nearest_node(self.G, (lat, lon))
    
    def add_route(self, route):
    
        """
        Add a route that we need to traverse
        to the graph.
        
        Args: a route returned by networkx.shortest_path
        Return: Nothing
        """
      
        if route is None:
          return
      
        nodep = None
        for node in route:
          edge_attr_dict={
              "id" : self.edge_count, 
              "weight" : 1    #This is a very temporary hack
          } 

          if nodep:
            self.g.add_node(node, attr_dict=self.G.nodes[node])
            self.g.add_node(nodep, attr_dict=self.G.nodes[nodep])
            self.g.add_edge(nodep, node, **edge_attr_dict)

          nodep = node
          self.edge_count+=1
        
    def solve(self, edge_weight='distance', verbose=False):
    
        """
        Solve the Chinese Postman Problem on this graph.
        
        Args: edge weight type, whether or not to print progress
        Return: A route consisting of node indexes
        """
    
        logger_cpp = logging.getLogger('{0}.{1}'.format(__name__, 'cpp'))
        logger_cpp.disabled = not verbose

        logger_cpp.info('get augmenting path for odd nodes')
        odd_nodes = get_odd_nodes(self.g)
        odd_node_pairs = list(itertools.combinations(odd_nodes, 2))
        odd_node_pairs_shortest_paths = get_shortest_paths_distances(self.g, odd_node_pairs, edge_weight)
        g_odd_complete = create_complete_graph(odd_node_pairs_shortest_paths, flip_weights=True)

        print("COMPLETED ODD GRAPH")
        print(g_odd_complete)
        
        logger_cpp.info('Find min weight matching using blossom algorithm')
        odd_matching = dedupe_matching(nx.algorithms.max_weight_matching(g_odd_complete, True))

        logger_cpp.info('add the min weight matching edges to g')
        g_aug = add_augmenting_path_to_graph(self.g, odd_matching)

        logger_cpp.info('get eulerian circuit route')
        circuit = list(create_eulerian_circuit(g_aug, self.g, self.start_node))

        return circuit