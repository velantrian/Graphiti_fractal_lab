from pathlib import Path
import shlex

import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE_REQUIREMENTS = {"requirements.txt", "requirements-lab.txt"}
CACHE_REQUIREMENTS = CORE_REQUIREMENTS | {"constraints-ci.txt"}


def _load_ci_workflow():
    # BaseLoader avoids YAML 1.1 coercing GitHub Actions' `on` key to True.
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(workflow, dict)
    assert isinstance(workflow.get("on"), dict)
    return workflow


def _run_commands(steps):
    for step in steps:
        script = step.get("run")
        if not isinstance(script, str):
            continue
        script = script.replace("\\\r\n", " ").replace("\\\n", " ")
        for line in script.splitlines():
            if not line.strip():
                continue
            command = []
            for token in shlex.split(line, comments=True):
                if token in {";", "&&", "||", "|"}:
                    if command:
                        yield command
                        command = []
                else:
                    command.append(token)
            if command:
                yield command


def _pip_install_arguments(command):
    if command[:4] == ["python", "-m", "pip", "install"]:
        return command[4:]
    if command[:2] == ["pip", "install"]:
        return command[2:]
    return None


def _has_option(arguments, value, *options):
    attached = {form for option in options for form in (f"{option}{value}", f"{option}={value}")}
    return any(
        token in attached
        or (token in options and index + 1 < len(arguments) and arguments[index + 1] == value)
        for index, token in enumerate(arguments)
    )


def _make_target(command, target):
    return (
        command[:1] == ["make"]
        and "PYTHON=python" in command[1:]
        and target in command[1:]
    ) or (command[:2] == ["PYTHON=python", "make"] and target in command[2:])


def _cache_paths(value):
    entries = value.splitlines() if isinstance(value, str) else value
    return {str(entry).strip() for entry in entries or [] if str(entry).strip()}


def _core_contracts_policy_is_valid(workflow):
    # This also verifies the GitHub Actions `on` key survived YAML parsing as a string key.
    if not isinstance(workflow.get("on"), dict):
        return False
    jobs = workflow.get("jobs")
    job = jobs.get("core-contracts") if isinstance(jobs, dict) else None
    if not isinstance(job, dict):
        return False

    strategy = job.get("strategy")
    matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
    versions = matrix.get("python-version") if isinstance(matrix, dict) else None
    if not isinstance(versions, list) or not {"3.10", "3.12"} <= set(versions):
        return False

    steps = job.get("steps")
    if not isinstance(steps, list):
        return False
    setup_ok = any(
        isinstance(step, dict)
        and str(step.get("uses", "")).startswith("actions/setup-python@")
        and isinstance(step.get("with"), dict)
        and step["with"].get("python-version") == "${{ matrix.python-version }}"
        and step["with"].get("cache") == "pip"
        and CACHE_REQUIREMENTS <= _cache_paths(step["with"].get("cache-dependency-path"))
        for step in steps
    )

    commands = list(_run_commands(steps))
    constrained_requirements = set()
    for command in commands:
        arguments = _pip_install_arguments(command)
        if arguments is not None and _has_option(
            arguments, "constraints-ci.txt", "-c", "--constraint"
        ):
            constrained_requirements.update(
                requirement
                for requirement in CORE_REQUIREMENTS
                if _has_option(arguments, requirement, "-r", "--requirement")
            )

    has_pip_check = any(
        command[:4] == ["python", "-m", "pip", "check"]
        or command[:2] == ["pip", "check"]
        for command in commands
    )
    has_collection = any(_make_target(command, "test-collect") for command in commands)
    has_contracts = any(_make_target(command, "test-contracts") for command in commands)
    return (
        setup_ok
        and CORE_REQUIREMENTS <= constrained_requirements
        and has_pip_check
        and has_collection
        and has_contracts
    )


def test_graphiti_runtime_is_pinned_to_current_reviewed_release():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "graphiti_core==0.29.3" in requirements


def test_neo4j_docker_is_pinned_to_reviewed_526_lts_patch():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "image: neo4j:5.26.29-community" in compose
    assert "image: neo4j:5.26-community" not in compose


def test_research_technologies_are_not_silently_runtime_dependencies():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8").lower()
    active = requirements + "\n" + compose

    research_dependencies = (
        "psycopg",
        "pgvector",
        "graphrag",
        "openspg",
        "dowhy",
        "causal-learn",
        "causal_learn",
        "graphdatascience",
        "kuzu",
        "ladybugdb",
        "ladybug-db",
    )
    for research_dependency in research_dependencies:
        assert research_dependency not in active


def test_reviewed_ci_constraints_pin_direct_runtime_dependencies():
    constraints = (ROOT / "constraints-ci.txt").read_text(encoding="utf-8")
    required_pins = (
        "graphiti_core==0.29.3",
        "python-dotenv==1.2.3",
        "neo4j==5.28.5",
        "pytest==9.1.1",
        "pytest-asyncio==1.4.0",
        "pydantic==2.13.5",
        "pydantic-settings==2.15.0",
        "fastapi==0.141.1",
        "uvicorn==0.52.4",
        "python-multipart==0.0.32",
        "openai==3.6.0",
        "httpx==0.28.1",
        "pathspec==1.1.1",
    )
    for pin in required_pins:
        assert pin in constraints


def test_other_automated_validation_workflows_install_reviewed_constraints():
    # ci.yml has a job-scoped semantic guard below; keep this text check for other workflows.
    workflow_paths = (
        ".github/workflows/neo4j-integration.yml",
        ".github/workflows/provider-e2e.yml",
        ".github/workflows/provenance-dry-run.yml",
        ".github/workflows/external-validation.yml",
    )
    for workflow_path in workflow_paths:
        workflow = (ROOT / workflow_path).read_text(encoding="utf-8")
        assert "-c constraints-ci.txt -r requirements.txt" in workflow
        assert "python -m pip check" in workflow


def test_core_contracts_dependency_policy_is_job_scoped():
    assert _core_contracts_policy_is_valid(_load_ci_workflow())


def test_core_contracts_guard_accepts_equivalent_shell_and_cache_formatting():
    workflow = _load_ci_workflow()
    job = workflow["jobs"]["core-contracts"]
    install = next(step for step in job["steps"] if "pip install" in step.get("run", ""))
    install["run"] = (
        "python -m pip install --upgrade pip\n"
        "python -m pip install \\\n"
        "  --requirement=requirements-lab.txt \\\n"
        "  --constraint constraints-ci.txt \\\n"
        "  -r requirements.txt\n"
        "python -m pip check"
    )
    setup = next(
        step for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/setup-python@")
    )
    setup["with"]["cache-dependency-path"] = "\n".join(
        sorted(_cache_paths(setup["with"]["cache-dependency-path"]), reverse=True)
    )
    job["strategy"]["matrix"]["python-version"] = ["3.12", "3.10", "3.13"]
    assert _core_contracts_policy_is_valid(workflow)
