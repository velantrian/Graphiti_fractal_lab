// Group ID audit (read-only)

// 1) Episodic distribution by group_id
MATCH (e:Episodic)
RETURN coalesce(e.group_id,'<NULL>') AS group_id, count(*) AS cnt
ORDER BY cnt DESC;

// 2) Episodic distribution by group_id + source_description
MATCH (e:Episodic)
RETURN coalesce(e.group_id,'<NULL>') AS group_id,
       coalesce(e.source_description,'<NULL>') AS source_description,
       count(*) AS cnt
ORDER BY cnt DESC
LIMIT 30;

// 3) Entity distribution by group_id
MATCH (e:Entity)
RETURN coalesce(e.group_id,'<NULL>') AS group_id, count(*) AS cnt
ORDER BY cnt DESC;

// 4) RELATES_TO distribution by group_id
MATCH ()-[r:RELATES_TO]->()
RETURN coalesce(r.group_id,'<NULL>') AS group_id, count(*) AS cnt
ORDER BY cnt DESC;

// 5) Missing group_id counts
CALL {
  MATCH (e:Episodic) RETURN 'Episodic' AS kind, sum(CASE WHEN e.group_id IS NULL THEN 1 ELSE 0 END) AS missing
  UNION ALL
  MATCH (e:Entity) RETURN 'Entity' AS kind, sum(CASE WHEN e.group_id IS NULL THEN 1 ELSE 0 END) AS missing
  UNION ALL
  MATCH ()-[r:RELATES_TO]->() RETURN 'RELATES_TO' AS kind, sum(CASE WHEN r.group_id IS NULL THEN 1 ELSE 0 END) AS missing
}
RETURN kind, missing;

// 6) Index sanity (Neo4j 5)
SHOW INDEXES
YIELD name, type, entityType, labelsOrTypes, properties
WHERE type IN ['FULLTEXT','VECTOR']
RETURN name, type, entityType, labelsOrTypes, properties
ORDER BY type, name;


