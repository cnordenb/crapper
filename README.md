# crapper

CRAP scores for Clojure, Java, Go, TypeScript, Rust, Python, and C. One run detects the language of each source file, applies that language's complexity and coverage rules, and writes the snapshot [uml-viewer](https://github.com/unclebob/uml-viewer) already reads.

The formula is the one from [crap4clj](https://github.com/unclebob/crap4clj), [crap4java](https://github.com/unclebob/crap4java), and [crap4go](https://github.com/unclebob/crap4go):

```text
CRAP = CC² × (1 − coverage)³ + CC
```

`CC` is cyclomatic complexity. `coverage` is the fraction of the function exercised by tests. A score of 1–5 is low risk, 5–30 is worth a look, and 30+ is complex and under-tested.

## Run

```bash
./crapper
```

On Windows, run `crapper.cmd` from PowerShell or cmd. `./crapper` works in Git Bash.

The first run creates `.venv` and installs the tool. From a project root it walks the tree, skips `test`, `spec`, `vendor`, `node_modules`, and `target`, and writes two results:

- a table on stdout, worst score first
- `.metrics/crap.edn`, replaced on every successful analysis

```bash
./crapper --no-coverage                  # complexity only; coverage is N/A
./crapper --use-existing-coverage        # read reports already on disk
./crapper src/demo/core.clj src/ui       # these files and trees
./crapper --changed                      # git additions and edits
./crapper combat                         # path fragment, same idea as crap4clj
./crapper --threshold 30                 # exit 2 when the worst score is higher
```

## Snapshot

`.metrics/crap.edn` has the same shape crap4clj writes:

```clojure
{:entries [{:name "place"
            :namespace "demo.Board"
            :complexity 3
            :coverage 75.0
            :crap 3.1}]}
```

uml-viewer groups entries by `:namespace` and joins each operation on `:name`. `nil` coverage is what `--no-coverage` writes: complexity only, and CRAP is `nil` too. A function the coverage report does not mention scores 0%.

| Language | `:namespace` | `:name` |
| --- | --- | --- |
| Clojure | the `ns` | the `defn` / `defn-` name |
| Java | `package.Class`, or `package.Outer.Inner` | the method name |
| Go | the package import path, or `import/path.Receiver` | the function or method name |
| TypeScript | the dotted module path, or `module.Class` | the function or method name |
| Rust | `crate::module`, or `crate::module::Type` | the function or method name |
| Python | the dotted module path, or `module.Class` | the function or method name |
| C | the file path without its extension, such as `src/util` | the function name |

Rename or move is a new entry. There is no identity matching across runs.

## What each language counts

Clojure follows crap4clj: `if` / `when` and their variants, `and`, `or`, `loop`, `catch`, and each clause of `cond`, `condp`, `case`, `cond->`, `cond->>`, `some->`, and `some->>`. Coverage prefers Cloverage's per-line form counts and falls back to LCOV.

Java follows crap4java: `if`, loops, `catch`, `?:`, each `switch` label, and `&&` / `||`. Constructors and methods inside anonymous classes are omitted. Coverage is JaCoCo's `INSTRUCTION` counter.

Go follows crap4go: `if`, `for`, `range`, each `switch` and `select` clause, and `&&` / `||`. Coverage is `go test -coverprofile`.

TypeScript, TSX, and JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`) use the same structural decisions as Java, including `&&` inside JSX, plus `??` and `?.`. Top-level functions, class methods, and top-level arrow functions are entries. An inline Express callback — `.get`, `.post`, `.put`, `.patch`, `.delete`, `.head`, `.options`, `.all`, `.use`, and `.route(path).get(...)` — is its own entry, named `GET /users`. A second callback on that same route is `GET /users#2`. Its decisions are not also charged to the enclosing function. Other nested callbacks stay inside the enclosing function. Coverage is LCOV. A function the report's `FNDA` record says never ran scores 0%, even when its declaration line ran as the module loaded. Otherwise, when the report has branch records (`BRDA`) inside a function, the score uses those branches; a function with no branches uses line hits. A `coverage` script is used as-is. A Vitest project runs `vitest --coverage` (installing `@vitest/coverage-v8` into `node_modules` when it is missing, without editing `package.json`). Other test scripts are wrapped in `c8`.

Rust counts `if`, loops, each `match` arm, `?`, and `&&` / `||`. `mod tests` is skipped. Coverage is LCOV from `cargo llvm-cov` or `cargo tarpaulin`, run in the nearest directory that contains `Cargo.toml`. When neither tool is installed, the run installs `cargo-llvm-cov`.

Python counts `if`, `elif`, `for`, `while`, `except`, each `match` case, a comprehension filter, a conditional expression, and each `and` / `or`. Nested functions stay inside the enclosing function. Coverage is LCOV from `coverage.py`, running pytest when the project uses it and `unittest` otherwise. `coverage` and `pytest` are installed into the project's interpreter when they are missing.

C (`.c`, `.h`) counts `if`, `for`, `while`, `do`, each `case` and `default` label, `?:`, and `&&` / `||`. Each function definition is an entry, including one inside an `#if` block. A GCC nested function stays inside the function that encloses it. A header and its source file share a namespace, so `src/util.h` and `src/util.c` are both `src/util`. `test_*.c`, `*_test.c`, and `CMakeFiles` directories are skipped. Coverage is LCOV, scored as TypeScript's is, and crapper does not produce it: C has no standard test command, and the build itself must be compiled with `--coverage`. See [C coverage](#c-coverage).

## Coverage commands

By default a run deletes the previous report for each language it is about to measure and regenerates it:

| Language | Command | Report |
| --- | --- | --- |
| Clojure | `clj -M:cov --lcov` (needs `deps.edn` or `bb.edn`) | `target/coverage/` |
| Java | JaCoCo Maven plugin `0.8.12` in each module with `pom.xml` | `target/site/jacoco/jacoco.xml` |
| Go | `go test ./... -coverprofile=...` | `target/coverage/go/coverage.out` |
| TypeScript | `npm run coverage`, or Vitest `--coverage`, or `npx c8 ... npm test` | `coverage/lcov.info` or `target/coverage/typescript/lcov.info` |
| Rust | `cargo llvm-cov` or `cargo tarpaulin`, per Cargo package | `target/coverage/rust/lcov.info` |
| Python | `coverage run` with pytest or unittest, then `coverage lcov` | `target/coverage/python/lcov.info` |
| C | none; the run reads the report already on disk | `target/coverage/c/lcov.info` |

A missing tool or a failed test run scores that language at 0% and still writes the snapshot. Pass `--coverage-command` to replace those defaults with one command of your own. `--no-coverage` is the run that leaves coverage and CRAP as N/A.

### C coverage

Build with gcc and `--coverage`, run the tests so gcov's data is written, and convert it to LCOV with [gcovr](https://gcovr.com) (`pip install gcovr`). For a CMake project with CTest, one `--coverage-command` does all of it:

```bash
./crapper --coverage-command "cmake -S . -B build -DCMAKE_C_FLAGS=--coverage && cmake --build build && ctest --test-dir build && cmake -E make_directory target/coverage/c && gcovr --root . --lcov target/coverage/c/lcov.info build"
```

gcovr does not create the report's directory, which is what `cmake -E make_directory` is for. On Windows, add `-G Ninja` to the first `cmake` so it builds with MinGW gcc: without a generator, CMake picks NMake and MSVC, whose builds gcov cannot read. A `--coverage-command` replaces every language's coverage run, so in a project with other languages it must write their reports too. Without the command, a run reads the C report from the last build and says so.

On Windows, `npm`, `npx`, `mvn`, and `node_modules/.bin/vitest` run through their `.cmd` files, and Python coverage uses `.venv\Scripts\python.exe`. The Clojure CLI's PowerShell module defines `clj` as a PowerShell command, which a coverage run cannot start: put a `clj.exe` or `clj.cmd` on `PATH`, or pass `--coverage-command`.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\pip install -e '.[dev]'
.venv\Scripts\pytest
```
