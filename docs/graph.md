# Graph Database Documentation

## Overview

NeuroGraph uses Neo4j as its graph database to store entities, relationships, and semantic connections. The graph enables rapid traversal, relationship discovery, and complex queries across the knowledge base.

## Node Types and Properties

### Entity Node Structure

All entities in the graph share common properties and type-specific properties.

#### Common Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | String | Yes | Unique identifier (e.g., ent_123abc) |
| `name` | String | Yes | Display name |
| `type` | String | Yes | Entity type (person, project, document, etc.) |
| `layer` | String | Yes | Memory layer (personal, shared, organization) |
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | Yes | Last update timestamp |
| `created_by` | String | Yes | User ID who created the entity |
| `confidence` | Float | Yes | Confidence score (0.0 - 1.0) |
| `embedding_id` | String | No | Reference to vector embedding |

### Entity Type Schemas

#### Person

```cypher
CREATE (p:Person:Entity {
    id: 'ent_person_001',
    name: 'John Doe',
    type: 'person',
    layer: 'shared',
    email: 'john.doe@example.com',
    role: 'Software Engineer',
    department: 'Engineering',
    location: 'San Francisco, CA',
    skills: ['Python', 'React', 'Neo4j'],
    created_at: datetime(),
    updated_at: datetime(),
    created_by: 'user_123',
    confidence: 0.95
})
```

#### Project

```cypher
CREATE (proj:Project:Entity {
    id: 'ent_project_001',
    name: 'NeuroGraph',
    type: 'project',
    layer: 'organization',
    description: 'Knowledge management system',
    status: 'active',
    start_date: date('2024-01-01'),
    end_date: date('2024-12-31'),
    budget: 100000,
    priority: 'high',
    tags: ['ai', 'knowledge-management', 'graph'],
    created_at: datetime(),
    updated_at: datetime(),
    created_by: 'user_123',
    confidence: 0.98
})
```

#### Document

```cypher
CREATE (doc:Document:Entity {
    id: 'ent_document_001',
    name: 'System Architecture',
    type: 'document',
    layer: 'shared',
    url: 'https://docs.example.com/architecture',
    format: 'markdown',
    size_bytes: 45600,
    version: '1.2.0',
    author: 'John Doe',
    tags: ['architecture', 'technical'],
    created_at: datetime(),
    updated_at: datetime(),
    created_by: 'user_123',
    confidence: 0.92
})
```

#### Event

```cypher
CREATE (evt:Event:Entity {
    id: 'ent_event_001',
    name: 'Q1 Planning Meeting',
    type: 'event',
    layer: 'shared',
    event_type: 'meeting',
    start_time: datetime('2024-01-15T14:00:00Z'),
    end_time: datetime('2024-01-15T15:30:00Z'),
    location: 'Conference Room A',
    attendees: ['user_123', 'user_456'],
    agenda: 'Discuss Q1 roadmap',
    created_at: datetime(),
    updated_at: datetime(),
    created_by: 'user_123',
    confidence: 0.90
})
```

#### Organization

```cypher
CREATE (org:Organization:Entity {
    id: 'ent_org_001',
    name: 'Acme Corporation',
    type: 'organization',
    layer: 'organization',
    industry: 'Technology',
    size: 500,
    founded: date('2010-01-01'),
    website: 'https://acme.com',
    headquarters: 'San Francisco, CA',
    created_at: datetime(),
    updated_at: datetime(),
    created_by: 'user_123',
    confidence: 1.0
})
```

## Relationship Types and Properties

### Common Relationship Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | String | Yes | Unique identifier (e.g., rel_123abc) |
| `created_at` | DateTime | Yes | Creation timestamp |
| `created_by` | String | Yes | User ID who created the relationship |
| `confidence` | Float | Yes | Confidence score (0.0 - 1.0) |
| `weight` | Float | No | Relationship strength (0.0 - 1.0) |

### Relationship Type Catalog

#### WORKS_ON

Person works on a project.

```cypher
CREATE (person)-[r:WORKS_ON {
    id: 'rel_001',
    role: 'Lead Developer',
    start_date: date('2024-01-01'),
    hours_per_week: 40,
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.95,
    weight: 0.9
}]->(project)
```

#### MANAGES

Person manages a project or team.

```cypher
CREATE (person)-[r:MANAGES {
    id: 'rel_002',
    since: date('2024-01-01'),
    team_size: 5,
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.98,
    weight: 1.0
}]->(project)
```

#### MENTIONS

Entity mentions another entity (from content analysis).

```cypher
CREATE (doc)-[r:MENTIONS {
    id: 'rel_003',
    context: 'Discussed in section 3',
    frequency: 5,
    created_at: datetime(),
    created_by: 'system',
    confidence: 0.85,
    weight: 0.7
}]->(person)
```

#### RELATES_TO

Generic relationship between entities.

```cypher
CREATE (entity1)-[r:RELATES_TO {
    id: 'rel_004',
    relationship_type: 'dependency',
    description: 'Project depends on library',
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.80,
    weight: 0.6
}]->(entity2)
```

#### AUTHORED_BY

Document or content authored by person.

```cypher
CREATE (doc)-[r:AUTHORED_BY {
    id: 'rel_005',
    date: date('2024-01-10'),
    version: '1.0',
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 1.0,
    weight: 1.0
}]->(person)
```

#### ATTENDED_BY

Event attended by person.

```cypher
CREATE (event)-[r:ATTENDED_BY {
    id: 'rel_006',
    role: 'participant',
    duration_minutes: 90,
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.92,
    weight: 0.8
}]->(person)
```

#### PART_OF

Entity is part of another entity (hierarchical).

```cypher
CREATE (subproject)-[r:PART_OF {
    id: 'rel_007',
    since: date('2024-01-01'),
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.95,
    weight: 0.9
}]->(project)
```

#### DEPENDS_ON

Entity depends on another entity.

```cypher
CREATE (project1)-[r:DEPENDS_ON {
    id: 'rel_008',
    dependency_type: 'technical',
    critical: true,
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.88,
    weight: 0.85
}]->(project2)
```

#### KNOWS

Person knows another person.

```cypher
CREATE (person1)-[r:KNOWS {
    id: 'rel_009',
    relationship: 'colleague',
    since: date('2023-01-01'),
    strength: 'strong',
    created_at: datetime(),
    created_by: 'user_123',
    confidence: 0.75,
    weight: 0.7
}]->(person2)
```

## Conflict Edge Representation

When conflicting information exists, conflict edges are created to track disagreements.

```cypher
// Original relationship
CREATE (entity1)-[r1:WORKS_ON {
    id: 'rel_010',
    role: 'Developer',
    confidence: 0.85
}]->(project)

// Conflicting information
CREATE (entity1)-[r2:WORKS_ON {
    id: 'rel_011',
    role: 'Lead Developer',
    confidence: 0.90
}]->(project)

// Create conflict relationship
CREATE (r1)-[c:CONFLICTS_WITH {
    id: 'conflict_001',
    reason: 'Different role assignments',
    detected_at: datetime(),
    resolution_status: 'pending'
}]->(r2)
```

### Conflict Resolution

```cypher
// Get conflicts for a relationship
MATCH (r1)-[c:CONFLICTS_WITH]-(r2)
WHERE r1.id = 'rel_010'
RETURN r1, c, r2

// Resolve conflict by choosing higher confidence
MATCH (r1)-[c:CONFLICTS_WITH]-(r2)
WHERE c.resolution_status = 'pending'
WITH r1, r2, c,
     CASE WHEN r1.confidence > r2.confidence THEN r1 ELSE r2 END as winner
DELETE c
SET winner.confidence = winner.confidence + 0.05
```

## Cypher Query Examples

### Basic Entity Queries

#### Find Entity by ID

```cypher
MATCH (e:Entity {id: 'ent_person_001'})
RETURN e
```

#### Find Entities by Type

```cypher
MATCH (e:Entity {type: 'person', layer: 'shared'})
RETURN e
LIMIT 50
```

#### Search Entities by Name

```cypher
MATCH (e:Entity)
WHERE e.name CONTAINS 'John'
RETURN e
```

### Relationship Queries

#### Get Entity with Direct Relationships

```cypher
MATCH (e:Entity {id: 'ent_person_001'})-[r]-(related)
RETURN e, r, related
```

#### Find All Projects a Person Works On

```cypher
MATCH (p:Person {id: 'ent_person_001'})-[r:WORKS_ON]->(proj:Project)
RETURN proj, r
ORDER BY r.start_date DESC
```

#### Find Team Members

```cypher
MATCH (proj:Project {id: 'ent_project_001'})<-[r:WORKS_ON]-(person:Person)
RETURN person, r
ORDER BY person.name
```

### Graph Traversal Algorithms

#### Find Shortest Path

```cypher
MATCH path = shortestPath(
    (start:Entity {id: 'ent_person_001'})-[*..5]-(end:Entity {id: 'ent_project_001'})
)
RETURN path
```

#### Find All Paths with Depth Limit

```cypher
MATCH path = (start:Entity {id: 'ent_person_001'})-[*1..3]-(end:Entity)
WHERE end.type = 'project'
RETURN path
LIMIT 10
```

#### Collaborative Filtering

Find people who work on similar projects:

```cypher
MATCH (p1:Person {id: 'ent_person_001'})-[:WORKS_ON]->(proj:Project)<-[:WORKS_ON]-(p2:Person)
WHERE p1 <> p2
WITH p2, COUNT(DISTINCT proj) as common_projects
RETURN p2, common_projects
ORDER BY common_projects DESC
LIMIT 10
```

#### Degree Centrality

Find most connected entities:

```cypher
MATCH (e:Entity)-[r]-()
WITH e, COUNT(r) as degree
RETURN e.name, e.type, degree
ORDER BY degree DESC
LIMIT 20
```

#### Community Detection

Find clusters of related entities:

```cypher
CALL gds.louvain.stream({
    nodeProjection: 'Entity',
    relationshipProjection: {
        RELATES_TO: {
            type: 'RELATES_TO',
            orientation: 'UNDIRECTED'
        }
    }
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS name, communityId
ORDER BY communityId
```

### Temporal Queries

#### Find Recent Entities

```cypher
MATCH (e:Entity)
WHERE e.created_at > datetime() - duration({days: 7})
RETURN e
ORDER BY e.created_at DESC
```

#### Find Active Projects

```cypher
MATCH (proj:Project)
WHERE proj.start_date <= date() AND (proj.end_date IS NULL OR proj.end_date >= date())
RETURN proj
```

#### Timeline Query

```cypher
MATCH (e:Event)
WHERE e.start_time >= datetime('2024-01-01T00:00:00Z')
  AND e.start_time < datetime('2024-02-01T00:00:00Z')
RETURN e
ORDER BY e.start_time
```

### Aggregation Queries

#### Count Entities by Type

```cypher
MATCH (e:Entity)
RETURN e.type, COUNT(e) as count
ORDER BY count DESC
```

#### Count Relationships by Type

```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, COUNT(r) as count
ORDER BY count DESC
```

#### Average Confidence by Layer

```cypher
MATCH (e:Entity)
RETURN e.layer, AVG(e.confidence) as avg_confidence
ORDER BY avg_confidence DESC
```

### Advanced Graph Patterns

#### Find Isolated Entities

```cypher
MATCH (e:Entity)
WHERE NOT (e)-[]-()
RETURN e
```

#### Find Circular Dependencies

```cypher
MATCH path = (start:Project)-[:DEPENDS_ON*]->(start)
RETURN path
```

#### Find Bridges (entities connecting communities)

```cypher
MATCH (e:Entity)-[r1]-(n1), (e)-[r2]-(n2)
WHERE n1 <> n2
WITH e, COUNT(DISTINCT n1) + COUNT(DISTINCT n2) as connections
WHERE connections > 10
RETURN e, connections
ORDER BY connections DESC
```

## Indexing Strategy

### Create Indexes

```cypher
// Primary key index
CREATE CONSTRAINT entity_id_unique ON (e:Entity) ASSERT e.id IS UNIQUE;

// Type index for fast filtering
CREATE INDEX entity_type FOR (e:Entity) ON (e.type);

// Layer index for access control
CREATE INDEX entity_layer FOR (e:Entity) ON (e.layer);

// Name index for search
CREATE INDEX entity_name FOR (e:Entity) ON (e.name);

// Composite index for common queries
CREATE INDEX entity_type_layer FOR (e:Entity) ON (e.type, e.layer);

// Temporal index
CREATE INDEX entity_created FOR (e:Entity) ON (e.created_at);

// Full-text search index
CREATE FULLTEXT INDEX entity_search FOR (e:Entity) ON EACH [e.name, e.description];

// Relationship type index
CREATE INDEX rel_type FOR ()-[r:RELATES_TO]-() ON (r.relationship_type);
```

### Index Usage

```cypher
// Query using indexes (explain plan)
EXPLAIN MATCH (e:Entity {type: 'person', layer: 'shared'})
WHERE e.name CONTAINS 'John'
RETURN e

// Full-text search
CALL db.index.fulltext.queryNodes('entity_search', 'machine learning')
YIELD node, score
RETURN node, score
ORDER BY score DESC
LIMIT 10
```

## Graph Statistics

### Database Statistics

```cypher
// Count all nodes
MATCH (n)
RETURN COUNT(n) as total_nodes

// Count all relationships
MATCH ()-[r]->()
RETURN COUNT(r) as total_relationships

// Database size
CALL apoc.meta.stats()
YIELD nodeCount, relCount, labelCount, relTypeCount
RETURN nodeCount, relCount, labelCount, relTypeCount

// Graph density
MATCH (n)
WITH COUNT(n) as nodes
MATCH ()-[r]->()
WITH nodes, COUNT(r) as rels
RETURN rels * 1.0 / (nodes * (nodes - 1)) as density
```

### Entity Statistics

```cypher
// Entities per layer
MATCH (e:Entity)
RETURN e.layer, COUNT(e) as count, AVG(e.confidence) as avg_confidence
ORDER BY count DESC

// Most connected entities
MATCH (e:Entity)-[r]-()
WITH e, COUNT(r) as degree
RETURN e.name, e.type, degree
ORDER BY degree DESC
LIMIT 20

// Orphaned entities
MATCH (e:Entity)
WHERE NOT (e)-[]-()
RETURN COUNT(e) as orphaned_count
```

## Graph Algorithms with GDS

### Install Graph Data Science Library

```cypher
// Check GDS version
CALL gds.version()

// Create in-memory graph projection
CALL gds.graph.project(
    'neurograph',
    'Entity',
    {
        RELATES_TO: {
            type: 'RELATES_TO',
            orientation: 'UNDIRECTED',
            properties: ['weight']
        }
    }
)
```

### PageRank

Find most important entities:

```cypher
CALL gds.pageRank.stream('neurograph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 20
```

### Betweenness Centrality

Find entities that bridge communities:

```cypher
CALL gds.betweenness.stream('neurograph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 20
```

### Node Similarity

Find similar entities based on connections:

```cypher
CALL gds.nodeSimilarity.stream('neurograph')
YIELD node1, node2, similarity
RETURN
    gds.util.asNode(node1).name AS entity1,
    gds.util.asNode(node2).name AS entity2,
    similarity
ORDER BY similarity DESC
LIMIT 50
```

## Graph Maintenance

### Cleanup Queries

```cypher
// Delete orphaned entities
MATCH (e:Entity)
WHERE NOT (e)-[]-() AND e.confidence < 0.5
DELETE e

// Remove duplicate relationships
MATCH (a)-[r:RELATES_TO]->(b)
WITH a, b, type(r) as rel_type, COLLECT(r) as rels
WHERE SIZE(rels) > 1
FOREACH (r IN TAIL(rels) | DELETE r)

// Update confidence scores
MATCH (e:Entity)
WHERE e.created_at < datetime() - duration({days: 365})
SET e.confidence = e.confidence * 0.8
```

### Backup and Restore

```bash
# Backup Neo4j database
neo4j-admin dump --database=neurograph --to=/backups/neurograph-2024-01-15.dump

# Restore from backup
neo4j-admin load --from=/backups/neurograph-2024-01-15.dump --database=neurograph --force
```

## Performance Optimization

### Query Optimization Tips

1. **Use Parameters**: Prevent query plan cache pollution
2. **Limit Results**: Always use LIMIT for open-ended queries
3. **Use Indexes**: Ensure queries use appropriate indexes
4. **Avoid Cartesian Products**: Be careful with multiple MATCH clauses
5. **Profile Queries**: Use PROFILE to identify bottlenecks

### Example Optimizations

```cypher
// Bad: Cartesian product
MATCH (p:Person), (proj:Project)
WHERE p.name = 'John' AND proj.status = 'active'
RETURN p, proj

// Good: Use relationships
MATCH (p:Person {name: 'John'})-[:WORKS_ON]->(proj:Project {status: 'active'})
RETURN p, proj

// Use parameters
MATCH (e:Entity {id: $entityId})
RETURN e
```

## Monitoring

### Key Metrics to Monitor

| Metric | Query | Target |
|--------|-------|--------|
| **Node Count** | `MATCH (n) RETURN COUNT(n)` | <10M |
| **Relationship Count** | `MATCH ()-[r]->() RETURN COUNT(r)` | <50M |
| **Avg Query Time** | Check logs | <100ms p95 |
| **Memory Usage** | Check `neo4j.conf` | <80% heap |
| **Page Cache Hit Ratio** | Metrics endpoint | >95% |

## Related Documentation

- [Architecture](./architecture.md) - Graph database role in system
- [Memory](./memory.md) - Memory layer using graph storage
- [Databases](./databases.md) - Neo4j configuration and setup
- [RAG](./rag.md) - Graph traversal in RAG pipeline
