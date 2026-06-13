import json
from pathlib import Path

from app.models.response_models import ProjectScanResult


class ProjectScannerAgent:
    name = "Project Scanner Agent"
    max_file_size_bytes = 250_000

    ignored_names = {
        ".env",
        ".git",
        "node_modules",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
        ".mypy_cache",
        ".ruff_cache",
        ".next",
        ".venv",
    }
    ignored_paths = {
        "backend/app/uploads",
        "backend/app/uploads/extracted",
        "backend/app/data",
    }
    source_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".md", ".json"}

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[3]

    def scan(self, user_input: str = "") -> ProjectScanResult:
        frameworks = self.detect_frameworks()
        package_manager = self.detect_package_manager()
        source_roots = self.detect_source_roots()
        key_files = self.detect_key_files()
        relevant_files, scanned_files_count, ignored_paths_count = self.find_relevant_files(user_input, key_files)
        build_commands = self.detect_build_commands()
        test_commands = self.detect_test_commands()

        return ProjectScanResult(
            frameworks_detected=frameworks,
            package_manager=package_manager,
            relevant_files=relevant_files,
            key_files=key_files,
            source_roots=source_roots,
            build_commands=build_commands,
            test_commands=test_commands,
            ignored_paths_count=ignored_paths_count,
            scanned_files_count=scanned_files_count,
            scan_summary=(
                f"Scanned {self.project_root.name}: {scanned_files_count} source/config file(s), "
                f"{ignored_paths_count} ignored path(s). Detected {', '.join(frameworks) or 'no known frameworks'} "
                f"and {package_manager or 'no package manager'}."
            ),
        )

    def detect_frameworks(self) -> list[str]:
        frameworks: list[str] = []
        if (self.project_root / "backend" / "app" / "main.py").exists():
            frameworks.append("FastAPI")
        package_json = self.project_root / "frontend" / "package.json"
        if package_json.exists():
            text = package_json.read_text(encoding="utf-8", errors="ignore").lower()
            if "vite" in text:
                frameworks.append("Vite")
            if "react" in text:
                frameworks.append("React")
        return frameworks

    def detect_package_manager(self) -> str | None:
        if (self.project_root / "frontend" / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (self.project_root / "frontend" / "yarn.lock").exists():
            return "yarn"
        if (self.project_root / "frontend" / "package-lock.json").exists():
            return "npm"
        if (self.project_root / "frontend" / "package.json").exists():
            return "npm"
        return None

    def detect_source_roots(self) -> list[str]:
        roots = [
            "backend/app",
            "backend/tests",
            "frontend/src",
            "docs",
            "plugins",
        ]
        return [root for root in roots if (self.project_root / root).exists()]

    def detect_key_files(self) -> list[str]:
        keys = [
            "README.md",
            "DEMO.md",
            "backend/app/main.py",
            "backend/app/api/routes.py",
            "backend/app/agents/master_agent.py",
            "backend/app/agents/project_scanner_agent.py",
            "backend/app/services/safe_file_editor.py",
            "backend/app/services/safe_command_runner.py",
            "backend/app/models/request_models.py",
            "backend/app/models/response_models.py",
            "backend/requirements.txt",
            "frontend/package.json",
            "frontend/src/App.jsx",
            "frontend/src/styles.css",
        ]
        return [path for path in keys if (self.project_root / path).exists()]

    def detect_build_commands(self) -> list[str]:
        commands: list[str] = []
        package_json = self._read_package_json()
        scripts = package_json.get("scripts", {}) if isinstance(package_json, dict) else {}
        if "build" in scripts:
            commands.append("npm run build")
        elif (self.project_root / "frontend" / "package.json").exists():
            commands.append("npm run build")
        return commands

    def detect_test_commands(self) -> list[str]:
        commands: list[str] = []
        if (self.project_root / "backend" / "tests").exists():
            commands.append("pytest")
        package_json = self._read_package_json()
        scripts = package_json.get("scripts", {}) if isinstance(package_json, dict) else {}
        if "test" in scripts:
            commands.append("npm test")
        return commands

    def find_relevant_files(self, user_input: str, key_files: list[str] | None = None) -> tuple[list[str], int, int]:
        terms = {token.strip(".,:;()[]{}").lower() for token in user_input.split() if len(token) > 3}
        scored: list[tuple[int, str]] = []
        scanned_files_count = 0
        ignored_paths_count = 0
        for path in self.project_root.rglob("*"):
            if self.is_ignored(path):
                ignored_paths_count += 1
                continue
            if not path.is_file():
                continue
            if path.stat().st_size > self.max_file_size_bytes:
                ignored_paths_count += 1
                continue
            relative = path.relative_to(self.project_root).as_posix()
            if path.suffix.lower() not in self.source_extensions:
                continue
            scanned_files_count += 1
            lower_relative = relative.lower()
            score = self._score_file(relative, terms)
            if score > 0:
                scored.append((score, relative))

        relevant = [path for _, path in sorted(scored, key=lambda item: (-item[0], item[1]))[:20]]
        if relevant:
            return relevant, scanned_files_count, ignored_paths_count

        defaults = key_files or [
            "frontend/src/App.jsx",
            "frontend/src/styles.css",
            "backend/app/agents/master_agent.py",
            "backend/app/api/routes.py",
            "backend/app/models/request_models.py",
            "backend/app/models/response_models.py",
        ]
        return [item for item in defaults if (self.project_root / item).exists()][:20], scanned_files_count, ignored_paths_count

    def _score_file(self, relative: str, terms: set[str]) -> int:
        lower_relative = relative.lower()
        score = 0
        if not terms:
            score += 1
        for term in terms:
            if term in lower_relative:
                score += 6
        if lower_relative in {
            "frontend/src/app.jsx",
            "frontend/src/styles.css",
            "backend/app/api/routes.py",
            "backend/app/agents/master_agent.py",
        }:
            score += 3
        if any(segment in lower_relative for segment in ("service", "agent", "route", "test", "api", "component", "style")):
            score += 2
        return score

    def is_ignored(self, path: Path) -> bool:
        parts = set(path.parts)
        if parts & self.ignored_names:
            return True
        relative = path.relative_to(self.project_root).as_posix()
        return any(relative == ignored or relative.startswith(f"{ignored}/") for ignored in self.ignored_paths)

    def _read_package_json(self) -> dict:
        path = self.project_root / "frontend" / "package.json"
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
