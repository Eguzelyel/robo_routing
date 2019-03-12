
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
	client = Socrata("data.cityofchicago.org", None)
	results = client.get("787j-mys9")
	df = pd.DataFrame.from_records(results)
	df = df[(df.status == "Open") | (df.status == "Open - Dup")]
	df = df[["latitude", "longitude"]]
	return df

#Find unique shortest path between one pothole and all other potholes
def short_path1(Chicago, Cpp, src, potholes):

  min_route = None
  min_route_cost = None
  
  #Find the node closest to the central pothole
  src_node = ox.get_nearest_node(Chicago, src)
  
  for index, row in potholes.iterrows():
    #Find the node closest to the other pothole
    dst = (float(row["latitude"]), float(row["longitude"]))
    dst_node = ox.get_nearest_node(Chicago, dst)

    #Compute the shortest path between the two
    try:
      route = nx.shortest_path(Chicago, src_node, dst_node)
    except:
      continue

    #If the route costs less to traverse, make it the shortest path
    #This is INCOMPLETE!
    if(min_route is None and route is not None):
      min_route = route
      break

  #Add the path to the edge list
  Cpp.add_route(min_route)
	

#Find the list of edges to use in the robot's route
def short_pathN(Chicago, Cpp, potholes):
  for index, row in potholes.iterrows():
    loc = (float(row["latitude"]), float(row["longitude"]))
    short_path1(Chicago, Cpp, loc, potholes)

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
