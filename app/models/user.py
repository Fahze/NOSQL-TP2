from py2neo import Graph, Node
from datetime import datetime

class User:
    def __init__(self, graph: Graph):
        self.graph = graph

    def create_user(self, name: str, email: str):
        user_node = Node("User", name=name, email=email, created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.graph.create(user_node)