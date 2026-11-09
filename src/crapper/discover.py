"""Find source files and decide which language each one is written in."""

import os
from pathlib import Path

EXTENSIONS = {
    ".clj": "clojure",
    ".cljc": "clojure",
    ".cljs": "clojure",
    ".bb": "clojure",
    ".java": "java",
    ".go": "go",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".js": "typescript",
    ".jsx": "typescript",
    ".mjs": "typescript",
    ".cjs": "typescript",
    ".rs": "rust",
    ".py": "python",
    ".c": "c",
    ".h": "c",
}

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "target",
    "dist",
    "build",
    "out",
    "coverage",
    ".metrics",
    "testdata",
    "__pycache__",
    ".clj-kondo",
    # CMake's compiler probe writes CMakeCCompilerId.c into any build directory.
    "CMakeFiles",
}

TEST_DIRS = {"test", "tests", "spec", "specs", "__tests__"}

GO_TEST_SUFFIX = "_test.go"
CLOJURE_TEST_SUFFIXES = ("_test.clj", "_test.cljc", "_test.cljs", "_test.bb")
JS_TEST_SUFFIXES = (
    ".test.ts",
    ".spec.ts",
    ".test.tsx",
    ".spec.tsx",
    ".test.mts",
    ".spec.mts",
    ".test.cts",
    ".spec.cts",
    ".test.js",
    ".spec.js",
    ".test.jsx",
    ".spec.jsx",
    ".test.mjs",
    ".spec.mjs",
    ".test.cjs",
    ".spec.cjs",
)
# `test_x.py` and `x_test.py`; Unity and cmocka name C tests the same way.
UNIT_TEST_EXTENSIONS = (".py", ".c")
UNIT_TEST_SUFFIXES = tuple(f"_test{extension}" for extension in UNIT_TEST_EXTENSIONS)


def language_of(path: str | Path) -> str | None:
    file_path = Path(path)
    name = file_path.name
    if name.endswith(".d.ts"):
        return None
    return EXTENSIONS.get(file_path.suffix)


def is_test_file(path: str | Path) -> bool:
    file_path = Path(path)
    name = file_path.name
    if name.endswith(GO_TEST_SUFFIX):
        return True
    if name.endswith(CLOJURE_TEST_SUFFIXES):
        return True
    if name.endswith(JS_TEST_SUFFIXES):
        return True
    if name == "conftest.py":
        return True
    if name.endswith(UNIT_TEST_SUFFIXES) or (
        name.startswith("test_") and name.endswith(UNIT_TEST_EXTENSIONS)
    ):
        return True
    return any(part in TEST_DIRS for part in file_path.parts)


def _walk(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames if name not in SKIP_DIRS and name not in TEST_DIRS
        ]
        for name in filenames:
            path = Path(dirpath) / name
            if language_of(path) is None or is_test_file(path):
                continue
            found.append(path)
    return found


def iter_source_files(roots: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for root in roots:
        for path in _walk(root):
            files.add(path.resolve())
    return sorted(files, key=lambda path: path.as_posix())
