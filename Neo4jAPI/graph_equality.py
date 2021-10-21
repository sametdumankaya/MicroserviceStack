from networkx.algorithms import isomorphism
from networkx.readwrite.graphml import read_graphml

g1 = read_graphml("131e6238-f1ae-4f12-bd9d-a933aaa7f09c.graphml")
g2 = read_graphml("ea91ce9d-c62d-48ad-92ae-2842407e582a.graphml")

print(isomorphism.is_isomorphic(g1, g2))
print(isomorphism.is_isomorphic(g1, g2, edge_match=isomorphism.numerical_edge_match('weight', 1)))