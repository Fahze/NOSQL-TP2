from py2neo import Graph, Node
from datetime import datetime

class Comment:
    def __init__(self, graph: Graph):
        self.graph = graph

    def create_comment(self, content: str):
        comment_node = Node("Comment", content=content, created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.graph.create(comment_node)