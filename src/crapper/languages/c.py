"""C functions and cyclomatic complexity.

Decision points are `if`, `for`, `while`, `do`, each `case` and `default`
label, `?:`, and `&&` / `||`: the structural decisions Java counts. C has no
namespaces, so the namespace is the file's path without its extension
(`src/util`), which a header shares with its source file. Definitions inside
`#if` blocks count. A GCC nested function stays inside the function that
encloses it. Coverage is LCOV, such as `gcovr --lcov` writes from gcov data.
"""

from pathlib import PurePosixPath

from crapper.languages.treesitter import (
    binary_logic,
    complexity,
    descendants,
    end_line,
    node_text,
    parse,
    start_line,
)
from crapper.model import Function

_DECISIONS = {
    "if_statement",
    "for_statement",
    "while_statement",
    "do_statement",
    "case_statement",
    "conditional_expression",
}


def _is_decision(node) -> bool:
    return node.type in _DECISIONS or binary_logic(node)


def _skip(_node) -> bool:
    return False


def _definitions(root):
    """Each function definition, without descending into one."""

    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == "function_definition":
            yield node
            continue
        stack.extend(reversed(node.children))


def _function_name(data: bytes, definition) -> str:
    """The declarator's first identifier, which is the name it declares.

    `static int *find(int *xs)` declares `find`, and so does
    `int (*find(int k))(void)`, which returns a function pointer: the walk is
    pre-order, so it meets the name before any parameter. When the name is
    missing, error recovery leaves an empty identifier, and this returns "".
    """

    declarator = definition.child_by_field_name("declarator")
    if declarator is None:
        return ""
    names = (node for node in descendants(declarator) if node.type == "identifier")
    return next((node_text(data, node) for node in names), "")


def _namespace(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).with_suffix("").as_posix()


def functions_in_source(
    source: str, path: str, project_root: str | None = None
) -> list[Function]:
    data, tree = parse(source, "c")
    namespace = _namespace(path)
    found: list[Function] = []
    for definition in _definitions(tree.root_node):
        name = _function_name(data, definition)
        if not name:
            continue
        found.append(
            Function(
                name=name,
                namespace=namespace,
                complexity=complexity(definition, _is_decision, _skip),
                start_line=start_line(definition),
                end_line=end_line(definition),
                path=path,
                language="c",
            )
        )
    return found
