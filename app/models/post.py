from py2neo import Graph, Node
from datetime import datetime

class Post:
    def __init__(self, graph: Graph):
        self.graph = graph

    def create_post(self, title: str, content: str):
        post_node = Node("Post", title=title, content=content, created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.graph.create(post_node)