
"""
This file predetermines the route a robot should take in order
to fill as many potholes as possible.
"""

import pandas as pd
from sodapy import Socrata
import networkx as nx
import osmnx as ox
from CppGraph import CppGraph

#Get the graph of Chicago
def chicago_graph():
	G = ox.graph_from_place("Chicago,IL, United States", network_type='drive')
	return G

#Download pothole coordinates of only open potholes and map to OSM nodes
def download_potholes():
	'''
	client = Socrata("data.cityofchicago.org", None)
	results = client.get("787j-mys9")
	df = pd.DataFrame.from_records(results)
	'''
	link = "https://data.cityofchicago.org/api/views/7as2-ds3y/rows.csv?accessType=DOWNLOAD"
	df = pd.read_csv(link)
	df = df[(df.status == "Open") | (df.status == "Open - Dup")]
	df = df[["latitude", "longitude"]]
	return df

#Find unique shortest path between one pothole and the one its closest to
def short_path1(Chicago, Cpp, src, dst, potholes):

	#Find the node closest to the central pothole
	src_node = ox.get_nearest_node(Chicago, src)

	#Find the node closest to the other pothole
	dst_node = ox.get_nearest_node(Chicago, dst)

	#Compute the shortest path between the two
	try:
		route = nx.shortest_path(Chicago, src_node, dst_node)
	except:
		print("Could not find path between the source and destination")
		raise

	#Add the path to the edge list
	Cpp.add_route(route)
	

#Find the list of edges to use in the robot's route
def short_pathN(Chicago, Cpp, potholes):

	#Get list of all coordinates

	#Compute the distance between one pothole and all other potholes
	

	#Find the shortest path
	for index, row in potholes.iterrows():
		dst = (float(row["latitude"]), float(row["longitude"]))
		short_path1(Chicago, Cpp, src, dst, potholes)

#Run the CPP over the edge list
def get_robo_route():

	print("Downloading Chicago")
	Chicago = chicago_graph()
	Cpp = CppGraph(Chicago)
	
	print("Downloading Potholes")
	potholes = download_potholes()
	
	print("Adding potholes to Chicago")
	short_pathN(Chicago, Cpp, potholes)
	
	print("Finding the route")
	route = Cpp.solve()
	
	fig, ax = ox.plot_graph_route(G, route, save=True, filename="graph")
	return route

get_robo_route()
