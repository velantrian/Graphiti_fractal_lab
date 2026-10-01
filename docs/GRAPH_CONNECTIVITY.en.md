# Graph Connectivity Diagnostics (Cypher without APOC)
> 🌐 🇬🇧 **English** · 🇷🇺 [Русский](./GRAPH_CONNECTIVITY.md)


These queries help determine how the data is connected and whether there are “bridges” between layers.

## 1. Connectivity Components Check (Simplified)
Shows how many groups of Entity nodes are not connected to one another through RELATES_TO or SAME_AS.

> **Note**: In version 2.0 (Graphiti-native), we do not create automatic `SAME_AS` relationships between different `group_id` values. Namespace isolation is expected behavior. Connectivity is provided at the search layer (Multi-Namespace Search).

```cypher
MATCH (e:Entity)
OPTIONAL MATCH (e)-[:RELATES_TO|SAME_AS]-(neighbor)
WITH e, count(neighbor) as degree
RETURN
    count(e) as total_entities,
    sum(case when degree = 0 then 1 else 0 end) as isolated_entities,
    avg(degree) as avg_degree
```

## 2. Finding Manual Bridges (SAME_AS)
Shows entities that were linked manually or remain from the old logic.
There should be few such relationships in the new architecture (only explicit exceptions).

```cypher
MATCH (n1:Entity)-[:SAME_AS]-(n2:Entity)
WHERE n1.group_id <> n2.group_id
RETURN
    n1.name as name,
    n1.group_id as layer1,
    n2.group_id as layer2,
    count(*) as connections
ORDER BY connections DESC
```

## 3. Connectivity through Facts (RELATES_TO)
Are there relationships between entities from different layers?

```cypher
MATCH (n1:Entity)-[r:RELATES_TO]-(n2:Entity)
WHERE n1.group_id <> n2.group_id
RETURN
    n1.group_id as from_layer,
    n2.group_id as to_layer,
    r.fact as fact
LIMIT 20
```

## 4. Authorship Check (User -> Episodic)
Verify that episodes are linked to a user.

```cypher
MATCH (u:User)-[:AUTHORED]->(e:Episodic)
RETURN u.name, count(e) as episodes_count
```

## 5. Finding “Orphaned” Episodes
Episodes that are not linked to any user.

```cypher
MATCH (e:Episodic)
WHERE NOT (:User)-[:AUTHORED]->(e)
RETURN count(e) as orphaned_episodes
```
