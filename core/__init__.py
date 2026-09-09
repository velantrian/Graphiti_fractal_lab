from .custom_entities import (
    ProjectEntity,
    TechnicalConceptEntity,
    DecisionEntity,
    TeamEntity,
    L3Summary,
)
from .config import get_config, settings
from .types import (
    SearchResult,
    ContextResult,
    MemoryType,
    EpisodeKind,
    EpisodeDict,
    EntityDict,
    EdgeDict,
)


def get_graphiti_client():
    # Lazy import чтобы тесты без graphiti_core не падали
    from .graphiti_client import get_graphiti_client as _impl

    return _impl()


__all__ = [
    "get_graphiti_client",
    "get_config",
    "settings",
    "ProjectEntity",
    "TechnicalConceptEntity",
    "DecisionEntity",
    "TeamEntity",
    "L3Summary",
    "SearchResult",
    "ContextResult",
    "MemoryType",
    "EpisodeKind",
    "EpisodeDict",
    "EntityDict",
    "EdgeDict",
]
