from pathlib import Path

from crapper.cli import run
from crapper.discover import is_test_file, iter_source_files, language_of
from crapper.languages.c import _function_name, functions_in_source

BRANCHY = """int classify(int x, int y)
{
    if (x > 0 && y > 0) {
        return 1;
    } else if (x < 0 || y < 0) {
        return -1;
    }
    for (int i = 0; i < x; i++) {
    }
    while (y--) {
    }
    do {
        x--;
    } while (x > 0);
    switch (x) {
    case 1:
    case 2:
        return 2;
    default:
        break;
    }
    return x ? 3 : 4;
}

int one(void) { return 1; }
"""


def _scored(source, path="src/grade.c"):
    return [
        (fn.name, fn.namespace, fn.complexity, fn.start_line, fn.end_line)
        for fn in functions_in_source(source, path)
    ]


def test_counts_each_branch_loop_label_and_condition():
    assert _scored(BRANCHY) == [
        ("classify", "src/grade", 12, 1, 23),
        ("one", "src/grade", 1, 25, 25),
    ]


def test_names_come_from_the_declarator_and_prototypes_are_not_entries():
    source = """#include "util.h"

int prototype(void);

static int *find(int *xs, int n) { return n > 0 ? xs : 0; }

int (*pick(int k))(void) { return 0; }

#ifdef FEATURE
void guarded(int a, int b) { if (a || b) {} }
#endif

int __attribute__((noinline)) slow(int x) { return x; }
"""
    assert [(name, cc) for name, _ns, cc, _start, _end in _scored(source)] == [
        ("find", 2),
        ("pick", 1),
        ("guarded", 3),
        ("slow", 1),
    ]


def test_a_definition_without_a_name_is_not_an_entry():
    class NoDeclarator:
        def child_by_field_name(self, _name):
            return None

    class Leaf:
        type = "primitive_type"
        children = []

    class OnlyTypes(NoDeclarator):
        def child_by_field_name(self, _name):
            return Leaf()

    assert _scored("int (*)(void) { return 0; }\nint kept(void) { return 1; }\n") == [
        ("kept", "src/grade", 1, 2, 2)
    ]
    assert _function_name(b"", NoDeclarator()) == ""
    assert _function_name(b"", OnlyTypes()) == ""


def test_a_nested_function_stays_inside_the_one_that_encloses_it():
    source = "int outer(int x) {\n  int inner(int y) { return y ? 1 : 0; }\n  return inner(x);\n}\n"
    assert _scored(source) == [("outer", "src/grade", 2, 1, 4)]


def test_the_namespace_is_the_path_without_its_extension():
    source = "static inline int clamp(int v) { return v < 0 ? 0 : v; }\n"
    assert _scored(source, "src/grade.h")[0][1] == "src/grade"
    assert _scored(source, "src\\core\\grade.c")[0][1] == "src/core/grade"
    assert _scored(source, "grade.c")[0][1] == "grade"


def test_c_sources_are_found_and_c_tests_and_cmake_probes_are_skipped(tmp_path):
    assert language_of("src/grade.c") == "c"
    assert language_of("src/grade.h") == "c"
    assert is_test_file("test_grade.c") is True
    assert is_test_file("grade_test.c") is True
    assert is_test_file("grade.c") is False
    assert is_test_file("latest_grade.c") is False
    source = tmp_path / "src" / "grade.c"
    probe = tmp_path / "cmake-build-debug" / "CMakeFiles" / "3.27.8" / "CompilerIdC" / "CMakeCCompilerId.c"
    for path in (source, probe):
        path.parent.mkdir(parents=True)
        path.write_text("int f(void) { return 0; }\n", encoding="utf-8")
    assert iter_source_files([tmp_path]) == [source.resolve()]


GRADE_C = """#include "grade.h"

char grade(int score)
{
    score = clamp(score);
    if (score >= 90) {
        return 'A';
    }
    if (score >= 75) {
        return 'B';
    }
    return score > 0 ? 'C' : 'F';
}

int unused(int flag)
{
    return flag ? 1 : 0;
}
"""

GRADE_H = """#ifndef GRADE_H
#define GRADE_H

static inline int clamp(int value)
{
    return value < 0 ? 0 : value;
}

char grade(int score);
int unused(int flag);

#endif
"""

# gcovr 8.8 --lcov from MinGW gcc 13 and gcov, with its absolute paths.
GCOVR_LCOV = """TN:GCOVR_report
SF:{root}/src/grade.c
VER:f09ce39bd65042f584a37bfd366b476e
FN:3,grade
FNDA:4,grade
FN:15,unused
FNDA:0,unused
FNF:2
FNH:1
BRDA:6,0,0,2
BRDA:6,0,1,2
BRDA:9,0,0,-
BRDA:9,0,1,2
BRDA:12,0,0,2
BRDA:12,0,1,-
BRF:6
BRH:4
DA:3,4,599a67f3bbf32a2d259de192ca75643b
DA:5,4,04c692d9e2d3cb03f92d847d324cbe8b
DA:6,4,1328f267c0044fda01952450b0b4d094
DA:7,2,5182aa03d27a8a1a690e009e002d9310
DA:9,2,ade4000869debc102ddb531f35ad9120
DA:10,0,1d65bde5fde4501d476a0da88f65e212
DA:12,2,b08ce27cfed57667e9e97eb714689d54
DA:15,0,e06006debcb1d968aa5f8a85c50190d5
DA:17,0,f0cc7f8e94f8212b880fad43455ccfbc
LH:6
LF:9
end_of_record
SF:{root}/src/grade.h
VER:a7d12965961cbe688d9eed6673011ab2
FN:4,clamp
FNDA:4,clamp
FNF:1
FNH:1
BRF:0
BRH:0
DA:4,4,0bcab83faf5f4dae5ebd7f5218c742b9
DA:6,4,9f9feda4f84232df48044a29c2a783a7
LH:2
LF:2
end_of_record
"""


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_gcovr_lcov_scores_c_functions(tmp_path):
    _write(tmp_path, "src/grade.c", GRADE_C)
    _write(tmp_path, "src/grade.h", GRADE_H)
    _write(
        tmp_path,
        "target/coverage/c/lcov.info",
        GCOVR_LCOV.format(root=tmp_path.resolve().as_posix()),
    )
    assert run(["--root", str(tmp_path), "--use-existing-coverage"]) == 0
    text = (tmp_path / ".metrics" / "crap.edn").read_text(encoding="utf-8")
    assert '{:name "grade", :namespace "src/grade", :complexity 4, :coverage 66.6667, :crap 4.5926}' in text
    assert '{:name "unused", :namespace "src/grade", :complexity 2, :coverage 0.0, :crap 6.0}' in text
    assert '{:name "clamp", :namespace "src/grade", :complexity 2, :coverage 100.0, :crap 2.0}' in text
