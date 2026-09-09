import os
import ast
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules', 
    '.cursor', 'neo4j', 'static', 'tests', 'benchmarks', 'migrations', 
    'agent-tools', 'terminals'
}

class ProjectAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: Path, root_path: Path):
        self.file_path = file_path
        self.root_path = root_path
        self.module_name = self._get_module_name(file_path, root_path)
        self.summary = {
            "path": str(file_path.relative_to(root_path)),
            "module": self.module_name,
            "description": "",
            "classes": [],
            "functions": [],
            "dependencies": []
        }
        self.internal_modules = set()

    def _get_module_name(self, path: Path, root: Path) -> str:
        rel = path.relative_to(root).with_suffix("")
        return str(rel).replace(os.sep, ".")

    def visit_Module(self, node):
        self.summary["description"] = (ast.get_docstring(node) or "").strip()
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        doc = (ast.get_docstring(node) or "").strip()
        self.summary["classes"].append({
            "name": node.name,
            "methods": methods,
            "description": doc
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Only top-level functions
        if isinstance(getattr(node, "parent", None), ast.Module) or not hasattr(node, "parent"):
            doc = (ast.get_docstring(node) or "").strip()
            self.summary["functions"].append({
                "name": node.name,
                "description": doc
            })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Import(self, node):
        for alias in node.names:
            self._add_dependency(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self._add_dependency(node.module, level=node.level)
        self.generic_visit(node)

    def _add_dependency(self, name: str, level: int = 0):
        # Resolve relative imports
        if level > 0:
            parts = self.module_name.split(".")
            base = ".".join(parts[:-level])
            name = f"{base}.{name}" if base else name
        
        # Check if it's an internal module
        # This is a simple heuristic: if it starts with one of our top-level packages
        top_packages = {'core', 'knowledge', 'queries', 'layers', 'experience', 'visualization', 'api'}
        first_part = name.split(".")[0]
        if first_part in top_packages or name in priority_files:
             if name not in self.summary["dependencies"] and name != self.module_name:
                self.summary["dependencies"].append(name)

priority_files = {'main', 'app', 'simple_chat_agent'}

def analyze_project(root_path: Path) -> Dict[str, Any]:
    project_map = {
        "project_name": "Graphiti Fractal (Mark)",
        "version": "2.0.0",
        "structure": []
    }
    
    # First pass: collect all python files to know what is internal
    py_files = []
    for path in root_path.rglob('*.py'):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        py_files.append(path)

    for file_path in py_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Manually add parent info for top-level detection
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    child.parent = node
            
            analyzer = ProjectAnalyzer(file_path, root_path)
            analyzer.visit(tree)
            project_map["structure"].append(analyzer.summary)
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    return project_map

if __name__ == "__main__":
    root = Path.cwd()
    logger.info(f"🚀 Starting project analysis in {root}")
    
    result = analyze_project(root)
    
    output_file = root / "project_structure.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Analysis complete. File saved to: {output_file}")

