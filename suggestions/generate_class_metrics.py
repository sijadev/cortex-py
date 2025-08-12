#!/usr/bin/env python3
"""
Generate class metrics for important classes in the Cortex project.
Outputs:
- class-metrics.json
- class-metrics.md

Metrics per class:
- file, class_name, loc, methods, static_methods, class_methods,
  attributes (class + instance), avg_method_loc, has_docstring,
  complexity (avg, max), public_methods, private_methods
"""
from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Union


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]  # .../cortex-py

# Targets (relative to repo root)
TARGET_FILES = [
    "cortex-cli/cortex/core/rule_based_linker.py",
    "cortex-cli/cortex/core/cross_vault_linker.py",
    "cortex-cli/cortex/cli/config/manager.py",
    "cortex-cli/cortex/integrations/cortex_ai/client.py",
]


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def node_loc(node: ast.AST) -> int:
    # Safe access to lineno/end_lineno (not always present for all nodes/static analyzers)
    lineno = getattr(node, "lineno", None)
    end_lineno = getattr(node, "end_lineno", None)
    if isinstance(lineno, int) and isinstance(end_lineno, int):
        return end_lineno - lineno + 1
    return 0


def method_complexity(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> int:
    # Simple cyclomatic complexity approximation
    complexity = 1
    branch_nodes = (
        ast.If,
        ast.For,
        ast.While,
        ast.Try,
        ast.With,
        ast.BoolOp,
        ast.IfExp,
        ast.ExceptHandler,
        ast.comprehension,
        ast.Match if hasattr(ast, "Match") else tuple(),
    )
    for n in ast.walk(func):
        if isinstance(n, branch_nodes):
            complexity += 1
        # Count boolean operators inside BoolOp
        if isinstance(n, ast.BoolOp):
            complexity += max(0, len(n.values) - 1)
    return complexity


def is_decorated(func: Union[ast.FunctionDef, ast.AsyncFunctionDef], name: str) -> bool:
    for d in func.decorator_list:
        if isinstance(d, ast.Name) and d.id == name:
            return True
        if isinstance(d, ast.Attribute) and d.attr == name:
            return True
    return False


def collect_instance_attrs(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
    attrs = []
    for n in ast.walk(func):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    attrs.append(t.attr)
        if isinstance(n, ast.AnnAssign):
            t = n.target
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                attrs.append(t.attr)
    return attrs


@dataclass
class MethodInfo:
    name: str
    loc: int
    complexity: int
    is_static: bool = False
    is_classmethod: bool = False


@dataclass
class ClassMetrics:
    file: str
    class_name: str
    loc: int
    has_docstring: bool
    methods: int
    public_methods: int
    private_methods: int
    static_methods: int
    class_methods: int
    avg_method_loc: float
    avg_complexity: float
    max_complexity: int
    class_attributes: List[str] = field(default_factory=list)
    instance_attributes: List[str] = field(default_factory=list)


def analyze_class(py_path: Path, cls: ast.ClassDef) -> ClassMetrics:
    methods: List[MethodInfo] = []
    class_attrs: List[str] = []
    instance_attrs: List[str] = []

    # class-level attributes
    for n in cls.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    class_attrs.append(t.id)
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            class_attrs.append(n.target.id)

    # methods and instance attrs via __init__
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            loc = node_loc(n)
            comp = method_complexity(n)
            mi = MethodInfo(
                name=n.name,
                loc=loc,
                complexity=comp,
                is_static=is_decorated(n, "staticmethod"),
                is_classmethod=is_decorated(n, "classmethod"),
            )
            methods.append(mi)
            if n.name == "__init__":
                instance_attrs.extend(collect_instance_attrs(n))

    total_methods = len(methods)
    public_methods = len([m for m in methods if not m.name.startswith("_")])
    private_methods = total_methods - public_methods
    static_methods = len([m for m in methods if m.is_static])
    class_methods = len([m for m in methods if m.is_classmethod])

    avg_method_loc = round(sum(m.loc for m in methods) / total_methods, 2) if total_methods else 0.0
    avg_complexity = round(sum(m.complexity for m in methods) / total_methods, 2) if total_methods else 0.0
    max_complexity = max((m.complexity for m in methods), default=0)

    cm = ClassMetrics(
        file=str(py_path.relative_to(REPO_ROOT)),
        class_name=cls.name,
        loc=node_loc(cls),
        has_docstring=ast.get_docstring(cls) is not None,
        methods=total_methods,
        public_methods=public_methods,
        private_methods=private_methods,
        static_methods=static_methods,
        class_methods=class_methods,
        avg_method_loc=avg_method_loc,
        avg_complexity=avg_complexity,
        max_complexity=max_complexity,
        class_attributes=sorted(set(class_attrs)),
        instance_attributes=sorted(set(instance_attrs)),
    )
    return cm


def analyze_file(py_path: Path) -> List[ClassMetrics]:
    src = read_file(py_path)
    tree = ast.parse(src)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    metrics = [analyze_class(py_path, c) for c in classes]
    return metrics


def write_reports(metrics: List[ClassMetrics]) -> None:
    # JSON
    json_path = HERE / "class-metrics.json"
    json_path.write_text(json.dumps([asdict(m) for m in metrics], indent=2), encoding="utf-8")

    # Markdown
    md_lines = [
        "# Klassen-Metriken (automatisch generiert)",
        "", "Hinweis: LOC und Komplexität sind Näherungswerte (AST-basiert).", "",
        "| Klasse | Datei | LOC | Methoden (pub/prv) | static | class | ⌀ LOC/Method | ⌀/max Komplexität | Attrs (class/instance) | Doku |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for m in metrics:
        md_lines.append(
            f"| {m.class_name} | {m.file} | {m.loc} | {m.methods} ({m.public_methods}/{m.private_methods}) | "
            f"{m.static_methods} | {m.class_methods} | {m.avg_method_loc} | {m.avg_complexity}/{m.max_complexity} | "
            f"{','.join(m.class_attributes) or '-'} / {','.join(m.instance_attributes) or '-'} | "
            f"{'✅' if m.has_docstring else '❌'} |"
        )
    (HERE / "class-metrics.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> None:
    all_metrics: List[ClassMetrics] = []
    for rel in TARGET_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        all_metrics.extend(analyze_file(path))

    # Filter to important classes only
    important = {"RuleBasedLinker", "LinkRule", "LinkMatch", "CrossVaultLinker", "CortexConfig", "CortexAIClient"}
    all_metrics = [m for m in all_metrics if m.class_name in important]

    write_reports(all_metrics)
    print(f"Generated metrics for {len(all_metrics)} classes:")
    for m in all_metrics:
        print(f" - {m.class_name} ({m.file})")


if __name__ == "__main__":
    main()
