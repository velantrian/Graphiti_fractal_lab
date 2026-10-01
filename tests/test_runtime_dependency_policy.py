from copy import deepcopy
from pathlib import Path
import shlex

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE_REQUIREMENTS = {"requirements.txt", "requirements-lab.txt"}
CACHE_REQUIREMENTS = CORE_REQUIREMENTS | {"constraints-ci.txt"}
POLICY_MARKERS = {"pip", "test-collect", "test-contracts"}
SHELL_OPERATOR_CHARS = ";&|"


def _load_ci_workflow():
    # BaseLoader avoids YAML 1.1 coercing GitHub Actions' `on` key to True.
    workflow = yaml.load(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(workflow, dict)
    assert isinstance(workflow.get("on"), dict)
    return workflow


def _shell_tokens(line):
    lexer = shlex.shlex(line, posix=True, punctuation_chars=SHELL_OPERATOR_CHARS)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return list(lexer)


def _has_shell_operator(tokens):
    return any(token and all(char in SHELL_OPERATOR_CHARS for char in token) for token in tokens)


def _run_commands(steps):
    """Parse simple command lines; reject unsupported operators in policy-bearing scripts."""
    commands = []
    for step in steps:
        script = step.get("run")
        if not isinstance(script, str):
            continue
        script = script.replace("\\\r\n", " ").replace("\\\n", " ")
        try:
            token_lines = [
                _shell_tokens(line)
                for line in script.splitlines()
                if line.strip()
            ]
        except ValueError:
            return None

        token_lines = [tokens for tokens in token_lines if tokens]
        policy_bearing = any(POLICY_MARKERS.intersection(tokens) for tokens in token_lines)
        has_unsupported_operator = any(_has_shell_operator(tokens) for tokens in token_lines)
        if has_unsupported_operator:
            # Ignore unrelated scripts such as the exact-target check; fail closed when
            # control flow or `;` could change how a policy command executes.
            if policy_bearing:
                return None
            continue
        commands.extend(token_lines)
    return commands


def _pip_install_arguments(command):
    if command[:4] == ["python", "-m", "pip", "install"]:
        return command[4:]
    if command[:2] == ["pip", "install"]:
        return command[2:]
    return None


def _has_option(arguments, value, *options):
    attached = {form for option in options for form in (f"{option}{value}", f"{option}={value}")}
    for index, token in enumerate(arguments):
        if token == "--":
            break
        if token in attached:
            return True
        if token in options and index + 1 < len(arguments) and arguments[index + 1] == value:
            return True
    return False


def _is_pip_check(command):
    return command[:4] == ["python", "-m", "pip", "check"] or command[:2] == ["pip", "check"]


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

    commands = _run_commands(steps)
    if commands is None:
        return False

    constrained_requirements = set()
    has_pip_check_after_required_install = False
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
        if _is_pip_check(command) and CORE_REQUIREMENTS <= constrained_requirements:
            has_pip_check_after_required_install = True

    has_collection = any(_make_target(command, "test-collect") for command in commands)
    has_contracts = any(_make_target(command, "test-contracts") for command in commands)
    return (
        setup_ok
        and CORE_REQUIREMENTS <= constrained_requirements
        and has_pip_check_after_required_install
        and has_collection
        and has_contracts
    )


def _install_step(workflow):
    return next(
        step
        for step in workflow["jobs"]["core-contracts"]["steps"]
        if "pip install" in step.get("run", "")
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
    install = _install_step(workflow)
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


@pytest.mark.parametrize(
    "mutation",
    [
        "remove-lab-requirement",
        "remove-constraints",
        "remove-lab-cache-input",
        "remove-python-3.10",
        "remove-python-3.12",
        "move-install-to-other-job",
        "pip-check-before-install",
        "conditional-or-install",
        "conditional-and-install",
        "options-after-terminator",
        "semicolon-in-policy-script",
    ],
)
def test_core_contracts_guard_rejects_policy_regressions(mutation):
    workflow = deepcopy(_load_ci_workflow())
    job = workflow["jobs"]["core-contracts"]
    install = _install_step(workflow)

    if mutation == "remove-lab-requirement":
        install["run"] = install["run"].replace("-r requirements-lab.txt", "", 1)
    elif mutation == "remove-constraints":
        install["run"] = install["run"].replace("-c constraints-ci.txt", "", 1)
    elif mutation == "remove-lab-cache-input":
        setup = next(
            step for step in job["steps"]
            if str(step.get("uses", "")).startswith("actions/setup-python@")
        )
        paths = _cache_paths(setup["with"]["cache-dependency-path"])
        setup["with"]["cache-dependency-path"] = "\n".join(
            sorted(paths - {"requirements-lab.txt"})
        )
    elif mutation.startswith("remove-python-"):
        job["strategy"]["matrix"]["python-version"].remove(
            mutation.removeprefix("remove-python-")
        )
    elif mutation == "move-install-to-other-job":
        line = next(
            line for line in install["run"].splitlines()
            if "-c constraints-ci.txt" in line
        )
        install["run"] = install["run"].replace(line, "", 1)
        workflow["jobs"]["docker-build"]["steps"].append({"run": line})
    elif mutation == "pip-check-before-install":
        install["run"] = (
            "python -m pip check\n"
            "python -m pip install -c constraints-ci.txt -r requirements.txt -r requirements-lab.txt"
        )
    elif mutation in {"conditional-or-install", "conditional-and-install"}:
        operator = "||" if mutation == "conditional-or-install" else "&&"
        condition = "true" if operator == "||" else "false"
        install["run"] = (
            f"{condition} {operator} python -m pip install -c constraints-ci.txt "
            "-r requirements.txt -r requirements-lab.txt\n"
            "python -m pip check"
        )
    elif mutation == "options-after-terminator":
        install["run"] = (
            "python -m pip install -- -c constraints-ci.txt -r requirements.txt "
            "-r requirements-lab.txt\npython -m pip check"
        )
    elif mutation == "semicolon-in-policy-script":
        install["run"] = (
            "python -m pip install -c constraints-ci.txt -r requirements.txt "
            "-r requirements-lab.txt; python -m pip check"
        )

    assert not _core_contracts_policy_is_valid(workflow), mutation
