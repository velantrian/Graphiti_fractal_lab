# Диагностика связности графа (Cypher без APOC)

Эти запросы помогают понять, как данные связаны между собой и есть ли "мосты" между слоями.

## 1. Проверка компонент связности (упрощенная)
Показывает, сколько есть групп Entity, которые не связаны друг с другом через RELATES_TO или SAME_AS.

> **Примечание**: В версии 2.0 (Graphiti-native) мы не создаем автоматических связей `SAME_AS` между разными `group_id`. Изоляция неймспейсов — ожидаемое поведение. Связность обеспечивается на уровне поиска (Multi-Namespace Search).

```cypher
MATCH (e:Entity)
OPTIONAL MATCH (e)-[:RELATES_TO|SAME_AS]-(neighbor)
WITH e, count(neighbor) as degree
RETURN 
    count(e) as total_entities,
    sum(case when degree = 0 then 1 else 0 end) as isolated_entities,
    avg(degree) as avg_degree
```

## 2. Поиск ручных мостов (SAME_AS)
Показывает сущности, которые были связаны вручную или остались от старой логики.
В новой архитектуре таких связей должно быть мало (только явные исключения).

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

## 3. Связность через факты (RELATES_TO)
Есть ли связи между сущностями из разных слоев.

```cypher
MATCH (n1:Entity)-[r:RELATES_TO]-(n2:Entity)
WHERE n1.group_id <> n2.group_id
RETURN 
    n1.group_id as from_layer, 
    n2.group_id as to_layer, 
    r.fact as fact
LIMIT 20
```

## 4. Проверка авторства (User -> Episodic)
Убедиться, что эпизоды привязаны к пользователю.

```cypher
MATCH (u:User)-[:AUTHORED]->(e:Episodic)
RETURN u.name, count(e) as episodes_count
```

## 5. Поиск "сиротских" эпизодов
Эпизоды, которые не привязаны ни к какому пользователю.

```cypher
MATCH (e:Episodic)
WHERE NOT (:User)-[:AUTHORED]->(e)
RETURN count(e) as orphaned_episodes
```