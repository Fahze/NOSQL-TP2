from py2neo import Graph, Node
from app.config import Config

graph = Graph(Config.NEO4J_URI, auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD))