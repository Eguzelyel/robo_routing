
import networkx as nx
from CppGraph import CppGraph

G = nx.MultiDiGraph()

for i in range(0, 10):
	G.add_node(i)

k=0
for i in range(0, 9):
	for j in range(i+1, 9):
		edge_attr_dict = {
			"id" : k,
			"weight" : 1
		}
		G.add_edge(i, j, attr_dict=edge_attr_dict)
		k+=1

Cpp = CppGraph(G)
Cpp.add_route([0, 1, 2])
Cpp.add_route([2, 0])
Cpp.add_route([1, 3, 5])
Cpp.add_route([5, 4, 1, 0])

print(Cpp.solve())