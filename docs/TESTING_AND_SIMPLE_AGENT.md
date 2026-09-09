# 🧪 ПОЛНЫЙ ГАЙД: Как Видеть и Тестировать Память

## Часть 1: Как Увидеть Что Сохраняется

### Способ 1: Neo4j Browser (Визуально в Браузере)

```bash
# 1. Убедись, что Neo4j работает
docker ps | grep neo4j

# 2. Открой браузер
http://localhost:7474

# 3. Логин: neo4j / password
# (как в .env)

# 4. Копируй и выполняй эти запросы:
```

#### Query 1: Все узлы
```cypher
MATCH (n) RETURN n LIMIT 100
```

**Результат:** Увидишь все 20+ узлов, их типы, свойства
```
PersonEntity: {name: "Sergey", role: "Developer", ...}
ProjectEntity: {name: "Fractal Memory", status: "Development", ...}
TechnicalConceptEntity: {name: "Knowledge Graph", level: 3, ...}
DecisionEntity: {decision_text: "Use vanilla Graphiti", status: "Active", ...}
TeamEntity: {team_name: "Core Team", members: ["Sergey", "Natasha"], ...}
```

#### Query 2: Все связи с типами
```cypher
MATCH (n)-[r]->(m) 
RETURN n.name as from, type(r) as relationship, m.name as to
LIMIT 50
```

**Результат:** Увидишь как связаны узлы
```
from              relationship        to
─────────────────────────────────────────────
Sergey            WORKS_ON            Fractal Memory
Fractal Memory    USES_TECHNOLOGY     Neo4j
Neo4j             IS_A                Graph Database
Sergey            DISCUSSES_WITH      Natasha
...
```

#### Query 3: Граф одного человека (со всеми его связями)
```cypher
MATCH (person:PersonEntity {name: "Sergey"})-[r]-(connected)
RETURN person, r, connected
```

**Результат:** Паучок с Sergey в центре и всеми связями
```
     Neo4j
      ↑
      │ USES_TECH
      │
  Fractal Memory ←→ Sergey ←→ Natasha
      ↓
    Graph Engine
```

#### Query 4: Что сохранилось за последние 24h?
```cypher
MATCH (e:Episode)
WHERE e.ingested_at > datetime.now() - duration('P1D')
RETURN e.name, e.episode_body, e.ingested_at
ORDER BY e.ingested_at DESC
```

#### Query 5: Все эпизоды и откуда они (source)
```cypher
MATCH (e:Episode)
RETURN 
  e.name as episode_name,
  e.source as source_type,
  e.source_description as description,
  size([(e)-[]-()]) as connection_count
```

---

### Способ 2: D3.js Visualization (Интерактивный Граф)

```bash
# 1. Сгенерируй JSON
python main.py viz-export

# Output:
# ✅ Exported to visualization/graph_data.json
#   Nodes: 20
#   Edges: 25

# 2. Открой файл в браузере
open visualization/visualization.html
# или: right-click на файл → Open with → Browser

# 3. Интерактивная графика:
# - Drag nodes = перемещать узлы
# - Hover over node = показать инфо
# - Zoom = колесо мыши
# - Силовой layout = автоматически раскладывает узлы
```

**Что видишь:**
```
    PersonEntity (красные)
         ↓
    ProjectEntity (голубые)
         ↓
    TechnicalConceptEntity (зелёные)
         ↓
    DecisionEntity (жёлтые)
```

Каждый узел = сущность  
Каждая линия = отношение  

---

### Способ 3: Текстовый Отчёт (в Терминале)

```bash
python main.py quality
```

**Вывод:**
```
📊 GRAPH QUALITY REPORT
═══════════════════════════════════════════════════════

Total Nodes: 23
Breakdown by Type:
    - PersonEntity: 2
    - ProjectEntity: 3
    - TechnicalConceptEntity: 5
    - DecisionEntity: 2
    - TeamEntity: 1
    - Episode: 3

Quality Checks:
✅ Total unique names: 23
✅ Duplicates: 0
✅ Temporal metadata: All episodes have timestamps
✅ Custom entity extraction: 100%
```

---

## Часть 2: Как Видеть Связи

### Все типы связей, которые создаются:

```cypher
# Возвращает все уникальные типы отношений
MATCH ()-[r]->() 
RETURN DISTINCT type(r) as relationship_type, count(r) as count
```

**Вывод:**
```
relationship_type       count
────────────────────────────────
MENTIONS               15
WORKS_ON               2
DISCUSSES_WITH         1
USES_TECHNOLOGY        3
IS_A                   2
INVOLVES               1
OCCURS_AT              1
```

### Что означает каждое отношение:

| Тип | Смысл | Пример |
|-----|-------|--------|
| MENTIONS | Сущность упоминается в эпизоде | Neo4j упоминается в эпизоде "Project Overview" |
| WORKS_ON | Человек работает на проекте | Sergey WORKS_ON Fractal Memory |
| DISCUSSES_WITH | Люди обсуждают | Sergey DISCUSSES_WITH Natasha |
| USES_TECHNOLOGY | Проект использует технологию | Fractal Memory USES_TECHNOLOGY Neo4j |
| IS_A | Классификация | Neo4j IS_A Graph Database |
| INVOLVES | Участвует в | Team INVOLVES Sergey |

---

## Часть 3: Простой Агент для Тестирования

Создадим минимальный агент, который:
1. ✅ Может добавлять информацию в память
2. ✅ Может извлекать контекст
3. ✅ Может отвечать с учётом памяти

### ⚠️ УСТАРЕЛО: Файл `simple_agent.py` был удален

**Примечание:** `simple_agent.py` больше не существует. Используйте:
- `SimpleChatAgent` для чата (см. `simple_chat_agent.py`)
- `MemoryOps` для операций с памятью (см. `core/memory_ops.py`)
- API эндпойнт `/chat` для тестирования через HTTP

### Устаревший код (только для справки): `simple_agent.py`

```python
#!/usr/bin/env python3
"""
Простой агент для тестирования памяти.
Это минимальный MVP для проверки что всё работает.
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# Импортируем наш модуль
from core.graphiti_client import GraphitiClient
from queries.context_builder import build_agent_context
from queries.quality_check import check_graph_quality
from layers.l1_consolidation import get_l1_context
from layers.l2_semantic import get_l2_semantic_context

load_dotenv()


class SimpleAgent:
    """Минимальный агент для тестирования памяти"""
    
    def __init__(self):
        self.graphiti = GraphitiClient(
            uri=os.getenv("NEO4J_URI"),
            user=os.getenv("NEO4J_USER"),
            password=os.getenv("NEO4J_PASSWORD"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.conversation_history = []
    
    async def initialize(self):
        """Инициализировать агент"""
        print("🤖 Initializing Simple Agent...")
        
        # Проверим что граф работает
        quality = await check_graph_quality(self.graphiti)
        print(f"   Graph has {quality['total_nodes']} nodes")
        print(f"   Nodes by type: {quality['node_breakdown']}")
        print("   ✅ Ready to chat!\n")
    
    async def remember(self, entity_name: str):
        """
        Вспомнить информацию об сущности
        """
        print(f"🧠 Remembering information about '{entity_name}'...")
        
        # L1: Недавняя информация
        l1 = await get_l1_context(self.graphiti, entity_name, hours_back=24)
        
        # L2: Паттерны отношений
        l2 = await get_l2_semantic_context(self.graphiti, entity_name)
        
        # Build context
        context = await build_agent_context(self.graphiti, entity_name)
        
        result = {
            "entity": entity_name,
            "L1_recent": l1,
            "L2_patterns": l2,
            "full_context": context
        }
        
        return result
    
    async def learn(self, message: str, tags: list = None):
        """
        Добавить новую информацию в память
        
        Args:
            message: Текст, который нужно запомнить
            tags: Теги для категоризации
        """
        print(f"📝 Learning: {message}")
        
        # Добавим в граф
        await self.graphiti.add_episode(
            name=f"Agent Learning {datetime.now().isoformat()}",
            episode_body=message,
            source_description="agent_learning",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Сохраним в историю
        self.conversation_history.append({
            "type": "learning",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        print("   ✅ Learned!\n")
    
    async def chat(self, user_message: str):
        """
        Ответить на вопрос с учётом памяти
        """
        print(f"👤 You: {user_message}\n")
        
        # Сохраним в историю
        self.conversation_history.append({
            "type": "question",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Найдём релевантный контекст из памяти
        # (это упрощённо - просто достаём что-то связанное)
        search_results = await self.graphiti._search(user_message, limit=5)
        
        if search_results.nodes:
            print(f"🤖 Based on my memory, here's what I know:\n")
            
            for node in search_results.nodes[:3]:
                print(f"   • {node.name} ({node.node_type})")
                
                # Если это проект - покажи компоненты
                if "Project" in node.node_type and hasattr(node, 'components'):
                    if node.components:
                        print(f"     Components: {', '.join(node.components)}")
                
                # Если это решение - покажи статус
                if "Decision" in node.node_type and hasattr(node, 'status'):
                    print(f"     Status: {node.status}")
            
            print()
        else:
            print(f"🤖 I don't have information about that yet.\n")
        
        # Сохраним ответ
        self.conversation_history.append({
            "type": "response",
            "content": "Based on my memory...",
            "timestamp": datetime.now().isoformat()
        })
    
    async def show_memory_graph(self):
        """Показать граф памяти"""
        print("\n📊 Memory Graph Structure:\n")
        
        quality = await check_graph_quality(self.graphiti)
        
        print(f"Total entities in memory: {quality['total_nodes']}")
        print(f"\nBreakdown by type:")
        for entity_type, count in quality['node_breakdown'].items():
            print(f"  • {entity_type}: {count}")
        
        print(f"\nTotal relationships: {quality.get('total_edges', 'unknown')}")


async def demo():
    """
    Демо работы агента
    Это то, что ты сможешь запустить и увидеть как всё работает
    """
    
    agent = SimpleAgent()
    await agent.initialize()
    
    # === ФАЗА 1: Посмотреть что уже в памяти ===
    print("=" * 60)
    print("PHASE 1: Exploring Existing Memory")
    print("=" * 60 + "\n")
    
    memory = await agent.remember("Sergey")
    print("📋 What I know about Sergey (L1):")
    print(memory["L1_recent"][:200] + "...\n")
    
    # === ФАЗА 2: Поговорить ===
    print("=" * 60)
    print("PHASE 2: Conversation with Memory")
    print("=" * 60 + "\n")
    
    await agent.chat("What project is Sergey working on?")
    
    await agent.chat("Who is involved in Fractal Memory?")
    
    await agent.chat("What technologies do we use?")
    
    # === ФАЗА 3: Научить новому ===
    print("=" * 60)
    print("PHASE 3: Teaching Agent New Information")
    print("=" * 60 + "\n")
    
    await agent.learn("Sergey and Natasha decided to use vanilla Graphiti first before optimizing with Redis buffers.")
    
    await agent.learn("The team is working remotely, with async communication via Telegram.")
    
    # === ФАЗА 4: Проверить что запомнилось ===
    print("=" * 60)
    print("PHASE 4: Verify Learning")
    print("=" * 60 + "\n")
    
    await agent.chat("What decision was made about optimization?")
    
    # === ФАЗА 5: Показать весь граф ===
    print("=" * 60)
    print("PHASE 5: Memory Graph Overview")
    print("=" * 60 + "\n")
    
    await agent.show_memory_graph()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    
    print("""
    📊 Next steps to explore:
    
    1. Open Neo4j Browser:
       http://localhost:7474
       User: neo4j / Password: password
       
       Run: MATCH (n) RETURN n LIMIT 100
       
    2. View Interactive Graph:
       Run: python main.py viz-export
       Open: visualization/visualization.html
       
    3. Check full memory state:
       Run: python main.py quality
    """)


if __name__ == "__main__":
    asyncio.run(demo())
```

---

## Как Использовать Этот Агент

### Запуск Демо
```bash
# 1. Убедись что Neo4j работает
docker ps | grep neo4j

# 2. Убедись что демо-данные загружены
python main.py seed

# 3. Запусти агент
# УСТАРЕЛО: python simple_agent.py (файл удален)
# Используйте: curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "test", "user_id": "test"}'
```

### Ожидаемый Вывод
```
🤖 Initializing Simple Agent...
   Graph has 23 nodes
   Nodes by type: {
     'PersonEntity': 2,
     'ProjectEntity': 3,
     'TechnicalConceptEntity': 5,
     'DecisionEntity': 2,
     'TeamEntity': 1
   }
   ✅ Ready to chat!

============================================================
PHASE 1: Exploring Existing Memory
============================================================

🧠 Remembering information about 'Sergey'...
   📋 What I know about Sergey (L1):
   Recent context (last 24h):
     • Sergey (PersonEntity)
     • Fractal Memory (ProjectEntity)
     • Natasha (PersonEntity)
   Key interactions:
     • Sergey WORKS_ON Fractal Memory

============================================================
PHASE 2: Conversation with Memory
============================================================

👤 You: What project is Sergey working on?

🤖 Based on my memory, here's what I know:

   • Fractal Memory (ProjectEntity)
     Components: Graph Engine, LLM Integration, Temporal Processing
   • Sergey (PersonEntity)
   • Neo4j (TechnicalConceptEntity)

...
```

---

## Проверка Ошибок

### Если что-то не работает:

#### ❌ "Connection refused"
```bash
# Проверь Neo4j
docker ps | grep neo4j

# Если не работает:
docker start neo4j

# Подожди 10 секунд
sleep 10

# Проверь доступ
curl http://localhost:7474
```

#### ❌ "No nodes found"
```bash
# Загрузи демо-данные
python main.py seed

# Проверь что загрузилось
python main.py quality
```

#### ❌ "GraphitiClient import error"
```bash
# Убедись что ты в правильной директории
pwd  # должно быть fractal_memory_v2/

# Установи зависимости
pip install -r requirements.txt

# Проверь путь
PYTHONPATH=. # УСТАРЕЛО: python simple_agent.py (файл удален)
# Используйте: curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "test", "user_id": "test"}'
```

---

## Что Видишь После Запуска

### В Терминале
- ✅ Начальное состояние графа
- ✅ Ответы агента на вопросы
- ✅ Что он выучил
- ✅ Финальное состояние графа

### В Neo4j Browser
- ✅ Все 25+ узлов
- ✅ Все связи между ними
- ✅ Визуальный граф

### В D3.js Visualization
- ✅ Интерактивный граф
- ✅ Перемещаемые узлы
- ✅ Hover информация
- ✅ Силовой layout

---

## Почему Это Работает (Объяснение)

### Без магии. Реально:

1. **Graphiti** (библиотека) делает:
   - Экстракцию сущностей из текста (через LLM)
   - Дедупликацию (нет дублей)
   - Управление отношениями

2. **Neo4j** (БД) делает:
   - Сохранение узлов и связей
   - Быстрый поиск
   - Консистентность (ACID)

3. **Наш код** делает:
   - L1-L3 слои (резюме, паттерны, абстракции)
   - Контекст-建筑для LLM
   - UI для визуализации

### Никаких фокусов. Всё проверяемо.

---

**Запусти и посмотри. Не верь на слово — вери на код.** 🚀