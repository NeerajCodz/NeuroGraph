#!/usr/bin/env python
"""Check Neo4j contents."""
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neurograph123'))
with driver.session() as session:
    # Check all labels
    result = session.run('MATCH (n) RETURN labels(n) as labels, count(*) as count')
    print("Node Labels:")
    for record in result:
        print(f"  {record['labels']}: {record['count']}")
    
    # Check Entity nodes with their properties
    result = session.run('''
        MATCH (e:Entity)
        RETURN e.id as id, e.name as name, e.type as type, 
               coalesce(e.layer, 'global') as layer
        LIMIT 10
    ''')
    print("\nEntity Nodes (first 10):")
    for record in result:
        print(f"  {record['name']} ({record['type']}): id={record['id']}, layer={record['layer']}")
    
    # Check relationships
    result = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(*) as count')
    print("\nRelationship Types:")
    for record in result:
        print(f"  {record['type']}: {record['count']}")

driver.close()
