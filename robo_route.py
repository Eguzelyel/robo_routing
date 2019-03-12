
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
	link = "https://data.cityofchicago.org/resource/_311-potholes.csv?$select=latitude,longitude,status"
	df = pd.read_csv(link)
	print(df.head())
	df = df[(df.status == "Open") | (df.status == "Open - Dup")]
	df = df[["latitude", "longitude"]]
	df = df.dropna(axis =0, subset=["longitude", "latitude"])
	print(df.head())
	return df

#Find shortest path between one pothole and the one its closest to
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

	#Get list of the (x, y)
	coords = []
	coords.append(Cpp.start)
	for i in potholes:
		coords.append()

	#Compute the (euclidean) distance between one pothole and all other potholes
	

	#Find the shortest path
	for index, row in potholes.iterrows():
		dst = (float(row["latitude"]), float(row["longitude"]))
		short_path1(Chicago, Cpp, src, dst, potholes)

#Run the CPP over the edge list
def get_robo_route(start=()):

	print("Downloading Chicago")
	#Chicago = chicago_graph()
	#Cpp = CppGraph(Chicago)
	#Cpp.set_start(start)
	
	print("Downloading Potholes")
	potholes = download_potholes()
	
	print("Adding potholes to Chicago")
	short_pathN(Chicago, Cpp, potholes)
	
	print("Finding the route")
	route = Cpp.solve()
	
	fig, ax = ox.plot_graph_route(G, route, save=True, filename="graph")
	return route

get_robo_route()
