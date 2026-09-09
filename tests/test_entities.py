from core.custom_entities import ProjectEntity, TechnicalConceptEntity


def test_project_entity_defaults():
    project = ProjectEntity(name="Fractal Memory")
    assert project.status == "Development"
    assert project.priority == 3
    assert project.owner == "Unknown"
    assert project.components == []


def test_technical_concept_defaults():
    concept = TechnicalConceptEntity(
        name="Graph Knowledge",
        description="Graph-based reasoning",
    )
    assert concept.abstraction_level == 2
    assert concept.related_concepts == []
    assert concept.implementation_status == "Theoretical"

