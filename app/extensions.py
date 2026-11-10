from __future__ import annotations

import importlib.util
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExtensionMetadata:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    permission_scope: List[str] = field(default_factory=list)
    enabled: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


class ExtensionSandbox:
    """Sandbox-friendly loader for extension modules in a trusted local environment."""

    def __init__(self, working_dir: str | Path) -> None:
        self.working_dir = Path(working_dir).expanduser().resolve()
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def load(self, extension_path: str | Path) -> ExtensionMetadata:
        path = Path(extension_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)

        spec = importlib.util.spec_from_file_location("trusted_extension", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load extension from {path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["trusted_extension"] = module
        spec.loader.exec_module(module)

        metadata = getattr(module, "METADATA", {})
        return ExtensionMetadata(
            id=metadata.get("id", path.stem),
            name=metadata.get("name", path.stem),
            version=metadata.get("version", "0.1.0"),
            description=metadata.get("description", ""),
            permission_scope=metadata.get("permission_scope", []),
            enabled=metadata.get("enabled", False),
            config=metadata.get("config", {}),
        )


class ExtensionManager:
    """Registry for local extension modules; enabled only by explicit allowlisting."""

    def __init__(self, sandbox: Optional[ExtensionSandbox] = None) -> None:
        self.sandbox = sandbox or ExtensionSandbox(tempfile.gettempdir())
        self.extensions: Dict[str, ExtensionMetadata] = {}

    def add(self, metadata: ExtensionMetadata) -> None:
        self.extensions[metadata.id] = metadata

    def enable(self, extension_id: str) -> bool:
        extension = self.extensions.get(extension_id)
        if extension is None:
            return False
        extension.enabled = True
        return True

    def disable(self, extension_id: str) -> bool:
        extension = self.extensions.get(extension_id)
        if extension is None:
            return False
        extension.enabled = False
        return True


# Real extension execution should run in a locked-down sandbox or container, not in-process.
