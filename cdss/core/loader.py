"""Load YAML-based Clinical Knowledge Packs from disk.

The loader intentionally performs no clinical decision making. It only turns a
knowledge-pack directory into an immutable-ish Python object that validator and
future engines can consume.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
from types import MappingProxyType
from typing import Any, Mapping


DEFAULT_PACK_FILES: tuple[str, ...] = (
    "metadata.yaml",
    "entities.yaml",
    "inference.yaml",
    "diagnosis.yaml",
    "treatment.yaml",
    "constraints.yaml",
    "backward.yaml",
    "scenarios.yaml",
    "followup.yaml",
    "workflow.yaml",
    "source_map.yaml",
)

RULE_GROUP_SUFFIX = "_rules"


@dataclass(frozen=True)
class KnowledgePack:
    """Loaded YAML files for one clinical knowledge pack."""

    root: Path
    files: Mapping[str, Mapping[str, Any]]

    def get_file(self, filename: str) -> Mapping[str, Any]:
        """Return a loaded YAML document by filename."""
        return self.files[filename]

    def iter_rule_groups(self) -> list[tuple[str, str, list[Mapping[str, Any]]]]:
        """Return `(filename, group_name, rules)` tuples for all YAML rule groups."""
        groups: list[tuple[str, str, list[Mapping[str, Any]]]] = []
        for filename, document in self.files.items():
            for key, value in document.items():
                if key.endswith(RULE_GROUP_SUFFIX) and isinstance(value, list):
                    groups.append((filename, key, value))
        return groups

    def rule_group_names(self) -> set[str]:
        """Return all rule-group names present in the pack."""
        return {group_name for _, group_name, _ in self.iter_rule_groups()}

    def rule_ids(self) -> list[str]:
        """Return rule IDs in pack order."""
        ids: list[str] = []
        for _, _, rules in self.iter_rule_groups():
            for rule in rules:
                rule_id = rule.get("id")
                if isinstance(rule_id, str):
                    ids.append(rule_id)
        return ids


class KnowledgePackLoader:
    """Filesystem loader for YAML Clinical Knowledge Packs."""

    def __init__(self, required_files: tuple[str, ...] = DEFAULT_PACK_FILES) -> None:
        self.required_files = required_files

    def load(self, pack_root: str | Path) -> KnowledgePack:
        """Load required YAML files from `pack_root`.

        Raises:
            FileNotFoundError: if the directory or a required file is absent.
            ValueError: if a YAML document is empty or not a mapping.
            RuntimeError: if no YAML backend can load the document.
        """
        root = Path(pack_root).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Knowledge pack directory not found: {root}")

        loaded: dict[str, Mapping[str, Any]] = {}
        for filename in self.required_files:
            file_path = root / filename
            if not file_path.is_file():
                raise FileNotFoundError(f"Required knowledge pack file is missing: {file_path}")

            document = self._load_yaml_file(file_path)

            if not isinstance(document, dict):
                raise ValueError(f"Knowledge pack file must contain a YAML mapping: {file_path}")
            loaded[filename] = MappingProxyType(document)

        return KnowledgePack(root=root, files=MappingProxyType(loaded))

    def _load_yaml_file(self, file_path: Path) -> Any:
        """Load one YAML file using PyYAML when installed, otherwise Ruby's YAML."""
        if _pyyaml_available():
            return _load_with_pyyaml(file_path)
        return _load_with_ruby_yaml(file_path)


def _load_with_pyyaml(file_path: Path) -> Any:
    yaml_module = importlib.import_module("yaml")
    with file_path.open("r", encoding="utf-8") as stream:
        return yaml_module.safe_load(stream)


def _load_with_ruby_yaml(file_path: Path) -> Any:
    ruby_script = (
        "require 'yaml'; "
        "require 'json'; "
        "puts JSON.generate(YAML.load_file(ARGV.fetch(0)))"
    )
    completed = subprocess.run(
        ["ruby", "-e", ruby_script, str(file_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _pyyaml_available() -> bool:
    return importlib.util.find_spec("yaml") is not None
