# NOSQL-TP2

install des requiremennts

```bash
pip install -r requirements.txt
```
Lancer neo4j via Docker
```bash
docker run --name neo4j -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j
```

Lancer le projet
```bash
python run.py
```
