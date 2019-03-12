
"""
This file predetermines the route a robot should take in order
to fill as many potholes as possible.

https://gps-coordinates.org/
https://github.com/gboeing/osmnx-examples
"""

import pandas as pd
from sodapy import Socrata
import networkx as nx
import osmnx as ox
from CppGraph import CppGraph

def download_chicago_graph():
	
	"""
	Download the graph of Chicago from Open Street Map and
	put into a NetworkX MultiDiGraph.
	
	Return: 
		A NetworkX MultiDiGraph.
	"""

	G = ox.graph_from_place("Chicago,IL, United States", network_type='drive')
	return G
	

def save_chicago_graph(G, path="chicago.xml"):

	"""
	Saves the graph of Chicago to a shape file, which
	can handle DiGraph format.
	
	Inputs:
		G: the graph of Chicago
		path: the location to save this graph to
	"""

	ox.save_graphml(G, filename=path)


def update_chicago_graph(path="chicago.xml"):

	"""
	Updates the data in the saved graph of Chicago.
	
	Inputs:
		path: the location of the Chicago graph on your disk
	"""

	Chicago = download_chicago_graph()
	save_chicago_graph(Chicago, path)
	

def open_chicago_graph(path="chicago.xml"):
	
	"""
	Opens the saved graph of Chicago and returns a
	NetworkX DiGraph of Chicago.
	
	Return:
		A NetworkX DiGraph of Chicago
	"""
	
	return ox.load_gdf_shapefile(G, filename=path)


def download_potholes():

	"""
	Download a CSV of potholes from the Chicago Data Portal.
	The CSV will have two rows when it is returned:
		1. Latitude
		2. Longitude
	These values are the coordinates of potholes in Chicago.
	
	Return:
		A pandas data frame of locations of potholes in Chicago
	"""

	link = "https://data.cityofchicago.org/api/views/7as2-ds3y/rows.csv?accessType=DOWNLOAD"
	df = pd.read_csv(link)
	df = df[(df.STATUS == "Open") | (df.STATUS == "Open - Dup")]
	df = df[["LATITUDE", "LONGITUDE"]]
	df = df.dropna(axis =0, subset=["LATITUDE", "LONGITUDE"])
	return df
	

def save_potholes(df, path="potholes.csv"):
	
	"""
	This function saves the pothole data frame downloaded from
	the Chicago Data Portal in a CSV file.
	
	Input:
		df: The pothole data frame
		path: The location to save the data frame to
	"""
	
	df.to_csv(path)


def update_potholes(path="potholes.csv"):

	"""
	This function updates the pothole data frame stored locally.
	
	Input:
		path: The location of the pothole data stored locally
	"""
	
	df = download_potholes()
	save_potholes(df, path)
	

def open_potholes(path="potholes.csv"):

	"""
	This function opens the pothole data frame stored locally.
	
	Input:
		path: The location of the pothole data stored locally
	"""

	df = pd.read_csv(path)
	return df


def short_path1(Chicago, Cpp, src, dst, potholes):

	"""
	This function finds the shortest path between one pothole
	and the pothole who is closest to it. It adds the path to
	Cpp.
	
	Inputs:
		Chicago: a MultiDiGraph of Chicago
		Cpp: A CppGraph to add the shortest path to
		src: The source pothole
		dst: The pothole closest to the source pothole
	"""


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
	

def short_pathN(Chicago, Cpp, potholes):

	"""
	This function finds the set of edges to be traversed in the
	robot's route. It adds the edges to Cpp.
	
	Input:
		Chicago: A MultiDiGraph of Chicago
		Cpp: A CppGraph to add the edges to
		potholes: A pandas dataframe of pothole data
	"""

	#
	coords.append(Cpp.start)
	for i in potholes:
		coords.append()

	#Compute the (euclidean) distance between one pothole and all other potholes
	

	#Find the shortest path
	for index, row in potholes.iterrows():
		dst = (float(row["latitude"]), float(row["longitude"]))
		short_path1(Chicago, Cpp, src, dst, potholes)


def get_robo_route(start=(41.814884, -87.664603), chicago_path="chicago.xml", pothole_path="potholes.xml"):

	"""
	This function will compute the optimal route for
	a robot to take to fill potholes.
	
	Input:
		start: The location where the robot starts and ends at (the facility)
		chicago_path: The location of the graph of Chicago located locally
		pothole_path: The location of the graph of the pothole data located locally
	Return:
		An ordered list of nodes representing the route the robot will take
	"""

	#Acquire the graph of Chicago
	print("Opening Chicago")
	Chicago = open_chicago_graph(chicago_path)
	Cpp = CppGraph(Chicago)
	Cpp.set_start(start)
	
	#Acquire the set of all potholes that need to be filled
	print("Opening Potholes")
	potholes = open_potholes(pothole_path)
	
	#Get the shortest paths connecting the potholes and the robot facility
	print("Adding potholes to Chicago")
	short_pathN(Chicago, Cpp, potholes)
	
	#Find the optimal way to traverse the graph starting from the robot's facility
	print("Finding the route")
	route = Cpp.solve()
	
	#Save the route the robot will take as an image
	fig, ax = ox.plot_graph_route(G, route, save=True, filename="graph")
	return route

update_chicago_graph("D:/Documents/School/S19/MATH 497/robo_routing/chicago.xml")
#update_potholes("D:/Documents/School/S19/MATH 497/robo_routing/potholes.csv")
#open_potholes("D:/Documents/School/S19/MATH 497/robo_routing/potholes.csv")
