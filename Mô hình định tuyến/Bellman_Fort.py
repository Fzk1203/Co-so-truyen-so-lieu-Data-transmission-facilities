﻿class Graph:
    def __init__(self, size):
        self.adj_matrix = [[0] * size for _ in range(size)]
        self.size = size
        self.vertex_data = [''] * size

    def add_edge(self, u, v, weight):
        if 0 <= u < self.size and 0 <= v < self.size:
            self.adj_matrix[u][v] = weight
            #self.adj_matrix[v][u] = weight  # For undirected graph

    def add_vertex_data(self, vertex, data):
        if 0 <= vertex < self.size:
            self.vertex_data[vertex] = data

    def bellman_ford(self, start_vertex_data):
        start_vertex = self.vertex_data.index(start_vertex_data)
        distances = [float('inf')] * self.size
        predecessors = [None] * self.size
        distances[start_vertex] = 0

        for i in range(self.size - 1):
            for u in range(self.size):
                for v in range(self.size):
                    if self.adj_matrix[u][v] != 0:
                        if distances[u] + self.adj_matrix[u][v] < distances[v]:
                            distances[v] = distances[u] + self.adj_matrix[u][v]
                            predecessors[v] = u
                            print(f"Relaxing edge {self.vertex_data[u]}->{self.vertex_data[v]}, Updated distance to {self.vertex_data[v]}: {distances[v]}")

        # Negative cycle detection
        for u in range(self.size):
            for v in range(self.size):
                if self.adj_matrix[u][v] != 0:
                    if distances[u] + self.adj_matrix[u][v] < distances[v]:
                        return (True, None, None)  # Indicate a negative cycle was found

        return (False, distances, predecessors)  # Indicate no negative cycle and return distances
    
    def get_path(self, predecessors, start_vertex, end_vertex):
        path = []
        current = self.vertex_data.index(end_vertex)
        while current is not None:
            path.insert(0, self.vertex_data[current])
            current = predecessors[current]
            if current == self.vertex_data.index(start_vertex):
                path.insert(0, start_vertex)
                break
        return '->'.join(path)

g = Graph(8)

g.add_vertex_data(0, 'A')
g.add_vertex_data(1, 'B')
g.add_vertex_data(2, 'C')
g.add_vertex_data(3, 'D')
g.add_vertex_data(4, 'E')
g.add_vertex_data(5, 'F')
g.add_vertex_data(6, 'G')
g.add_vertex_data(7, 'H')
g.add_edge(0, 1, 2)  
g.add_edge(0, 3, 4)  
g.add_edge(1, 0, 2)  
g.add_edge(1, 2, -2)  
g.add_edge(1, 4, 2)   
g.add_edge(2, 4, 2)  
g.add_edge(2, 5, 1) 
g.add_edge(3, 0, 4)
g.add_edge(3, 4, 3)
g.add_edge(3, 7, 1)
g.add_edge(4, 1, 2) 
g.add_edge(4, 2, 2)
g.add_edge(4, 3, 3)
g.add_edge(4, 5, 3)
g.add_edge(4, 6, 1)
g.add_edge(5, 2, 1)
g.add_edge(5, 4, 3)
g.add_edge(5, 6, -1)
g.add_edge(6, 3, -3)
g.add_edge(6, 4, 1)
g.add_edge(6, 7, 4)
g.add_edge(7, 3, 1)
g.add_edge(7, 6, 4) 

# Running the Bellman-Ford algorithm from B to all vertices
print("\nThe Bellman-Ford Algorithm starting from vertex B:")
negative_cycle, distances, predecessors = g.bellman_ford('B')
if not negative_cycle:
    for i, d in enumerate(distances):
        if d != float('inf'):
            path = g.get_path(predecessors, 'B', g.vertex_data[i])
            print(f"{path}, Distance: {d}")
        else:
            print(f"No path from B to {g.vertex_data[i]}, Distance: Infinity")
else:
    print("Negative weight cycle detected. Cannot compute shortest paths.")