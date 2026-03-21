# TinyLanguage

TinyLanguage is a small Julia-inspired language with a Python implementation (interpreter + tooling) and multiple experimental backends (native/C, LLVM prototype, transpilers). The project is primarily a **learning playground** for language design, IR experiments, and cross-language interoperability—not a production SDK.

Note: The ideas largely come from me, but the code was generated with ChatGPT.

If you want a compact reference first:
- Language spec: [docs/language_spec.md](docs/language_spec.md)
- Tutorial: [docs/tutorial.md](docs/tutorial.md)
- Demo commands: [docs/demo_run_commands.md](docs/demo_run_commands.md)
- Python interop (FFI): [docs/python_interop.md](docs/python_interop.md)
- Backend coverage: [docs/backend_feature_matrix.md](docs/backend_feature_matrix.md)

---

## Table of contents

- [Quick start](#quick-start)
- [Language tour](#language-tour)
- [Backends](#backends)
- [Documentation map](#documentation-map)
- [Repository layout](#repository-layout)
- [Development](#development)
- [Status and closed tasks](#status-and-closed-tasks)
- [Roadmap](#roadmap)
- [Glossary](#glossary)

---

## Quick start

### Run a `.tiny` program

1. (Optional) Activate your virtual environment.
2. From the repository root, run any `.tiny` file (for example: [src_tiny/class_demo.tiny](src_tiny/class_demo.tiny)):

```bash
python src/tiny_language.py src_tiny/class_demo.tiny
```

You can also run via the compatibility module shim (optional):

```bash
python -m tiny_language src_tiny/class_demo.tiny
```

You should see:

```text
Hello, TinyLanguage!
```

If nothing appears, double-check you are running from the repository root and that you passed a `.tiny` file path.

### Run tests

```bash
python -m pytest
```

### VS Code: Launch-Aufruf für den Image Converter

Falls du den Launch-Aufruf für den Bildkonverter suchst: In `.vscode/launch.json` gibt es die Konfiguration **`Python: run image_composite_converter -> artifacts/converted_images`**. Sie startet das Modul `src.image_composite_converter` mit dem Arbeitsverzeichnis `${workspaceFolder}` und übergibt dabei direkt den Eingabeordner sowie die CSV/XML- und Ausgabe-Pfade.

Entspricht auf der Kommandozeile sinngemäß:

```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0000 \
  --end ZZ9999
```

Die vollständige CLI-Referenz inkl. Annotate-Modus, AC08-Regression-Workflow,
Positions-/Named-Argumenten und Vendor-Installationskommando steht in
[docs/image_converter_cli.md](docs/image_converter_cli.md).

### Run the “everything” runner

If you want a broad smoke test across demos and tools:

```bash
python src/run_all.py
```

---

## Language tour

### Mini tutorial: variables, control flow, and functions

```tiny
// Variables, arithmetic, printing
def a = 7 + 5 * 2;
def _unused1 = print(a);                // -> 17

// Declare and call functions
fn add(x, y) {
    return x + y;
}

def sum = add(a, 3);
def _unused2 = print(sum);

// If/while and mutation
def i = 0;
while (i < 3) {
    if (i == 1) { def _unused3 = print("in the middle"); }
    i = i + 1;
}

// Namespaces
namespace Math {
    fn inc(x) { return add(x, 1); }
}
def _unused4 = print(Math.inc(4));
```

### More building blocks

- Comparisons and strings: `>`, `>=`, `<`, `<=`, `==`, `!=` and string concatenation with `+`.
- Exponentiation: `^` accepts **integer exponents only**; for fractional exponents use `power(base, exponent)`.
- Heap and arrays:
  - `new(3)` allocates a pointer with three slots.
  - `new[1, 2, 3]` allocates an array on the heap.
  - `heap_get` / `heap_set` read and write.
  - `tag(ptr, "Type")` adds a runtime tag; `delete(ptr)` deletes the allocation.
- Destructuring: functions can return structs and callers can bind them with `{a, b} = f();` (all bindings must be used).
- Classes and operators: classes have fields/methods; operators can be overloaded.
- Concurrency: `spawn f(...)` starts a task; `join(task)` waits and returns the result.

### Demos worth running

Each demo is runnable and has expected output documented in the README and/or [docs/](docs/):

- Classes: [src_tiny/class_demo.tiny](src_tiny/class_demo.tiny)
- Operator overloading: [src_tiny/operator_overloading_demo.tiny](src_tiny/operator_overloading_demo.tiny)
- Namespaces: [src_tiny/namespace_demo.tiny](src_tiny/namespace_demo.tiny)
- Pattern matching / ADTs: [src_tiny/match_demo.tiny](src_tiny/match_demo.tiny)
- Imports/modules: see [docs/tutorial.md](docs/tutorial.md) and [docs/demo_run_commands.md](docs/demo_run_commands.md)
- Concurrency: [src_tiny/concurrency_demo.tiny](src_tiny/concurrency_demo.tiny)
- Heap pointers: [src_tiny/heap_pointer_demo.tiny](src_tiny/heap_pointer_demo.tiny)

---

## Backends

TinyLanguage currently ships multiple execution routes:

- **Interpreter** (default): parse → AST/IR → execute in Python
- **Python backend**: alternative execution path for comparison/testing
- **Native (C backend)**: emit a small C VM + bytecode, compile via `cc/clang/gcc` (see [docs/c_backend.md](docs/c_backend.md))
- **LLVM prototype**: optional IR emission path (experimental)

### Compile to a native executable (C backend)

Install a C compiler and ensure it is on your `PATH` (or set `TINYLANG_C_COMPILER`).

```bash
python -m tinyc_cli examples/c_backend/hello_world.tiny -o hello_world
./hello_world
```

To inspect the generated C without compiling:

```bash
python -m tinyc_cli examples/c_backend/hello_world.tiny --emit-c > hello_world.c
```

### Microbenchmarks

See [benchmarks/microbenchmarks.py](benchmarks/microbenchmarks.py) and [docs/performance_microbenchmarks.md](docs/performance_microbenchmarks.md) for deterministic short-running benchmarks that compare backends.

---

## Documentation map

### Getting started and tutorials
- [docs/tutorial.md](docs/tutorial.md) — setup + runnable demos + core constructs
- [docs/feature_cheat_sheet.md](docs/feature_cheat_sheet.md) — condensed feature reference
- [docs/demo_run_commands.md](docs/demo_run_commands.md) — copy/paste command list

### Language and stdlib references
- [docs/language_spec.md](docs/language_spec.md) — syntax/type/operator reference
- [docs/stdlib_compatibility.md](docs/stdlib_compatibility.md) — stdlib goals + deviations
- [docs/stdlib_extensions.md](docs/stdlib_extensions.md) — TinyLanguage-specific additions

### Interop
- [docs/python_interop.md](docs/python_interop.md) — FFI usage with demos and expected outputs
- [docs/cross_language_compatibility.md](docs/cross_language_compatibility.md) — portability notes + mappings
- [docs/rosetta_python_examples.md](docs/rosetta_python_examples.md) — Rosetta Code–style ports

### Tooling and debugging
- [docs/language_server_workflows.md](docs/language_server_workflows.md) — LSP workflows and demo calls
- [docs/debugger_workflows.md](docs/debugger_workflows.md) — VS Code stepping/launch guide
- [var/NotepadPP.xml](var/NotepadPP.xml) — Notepad++ syntax highlighting for `.tiny` files
- [docs/fuzzing.md](docs/fuzzing.md) — Hypothesis-based fuzz tests
- [docs/building_executables.md](docs/building_executables.md) — PyInstaller notes
- [docs/git_conflict_troubleshooting.md](docs/git_conflict_troubleshooting.md) — practical merge/rebase checklist

### Internals and performance
- [docs/c_backend.md](docs/c_backend.md) — C backend CLI and supported subset
- [docs/native_compiler.md](docs/native_compiler.md) — native backend workflow + limits
- [docs/native_ir.md](docs/native_ir.md) — native backend IR
- [docs/backend_feature_matrix.md](docs/backend_feature_matrix.md) — feature coverage by backend
- [docs/structured_concurrency.md](docs/structured_concurrency.md) — cancellation/token design

### Planning
- [docs/expansion_roadmap.md](docs/expansion_roadmap.md)
- [docs/self_hosting_port_plan.md](docs/self_hosting_port_plan.md)
- [docs/ac08_improvement_plan.md](docs/ac08_improvement_plan.md)

---

## Repository layout

- [src/](src/) — Python implementation (parser, interpreter, tooling)
- [src_tiny/](src_tiny/) — TinyLanguage programs (demos + self-hosting prototypes)
- [stdlib/](stdlib/) — standard library sources
- [tests/](tests/) — unit and regression tests
- [benchmarks/](benchmarks/) — microbenchmarks and performance helpers
- [docs/](docs/) — documentation
- [vscode-extension/](vscode-extension/) — VS Code extension + debug adapter prototype

---

## Development

### Helpful commands

```bash
# Run one file
python src/tiny_language.py path/to/program.tiny

# Module shim (optional; same behavior as src/tiny_language.py)
python -m tiny_language path/to/program.tiny

# Run with the Python CLI wrapper (switch backends)
python src/tiny_language_cli.py path/to/program.tiny --backend interpreter
python src/tiny_language_cli.py --file - --backend interpreter < path/to/program.tiny
python src/tiny_language_cli.py --source "print(1+2);" --backend interpreter
python src/tiny_language_cli.py -e "print(1+2);" --backend interpreter
python src/tiny_language_cli.py --file path/to/program.tiny --native-backend
python src/tiny_language_cli.py --file path/to/program.tiny -- --flag value

# Run tests
python -m pytest
```

For a fuller walkthrough of interpreter, wrapper, and native backend CLI usage,
see [docs/cli_workflows.md](docs/cli_workflows.md).

### Debugging and tracing

If you suspect stepping/breakpoints or interpreter flow issues, environment variables enable trace logging:

- `TINYLANG_TRACE_LOG=/tmp/tiny_trace.log`
- `TINYLANG_TRACE_HEARTBEAT_SECS=1.0`
- `TINYLANG_TRACE_EVERY_STATEMENT=1`
- `TINYLANG_TRACE_STDOUT=1`

For VS Code debug adapter logging:

- `TINYLANGUAGE_DAP_LOG=/tmp/tiny_dap.log`
- `TINYLANGUAGE_DAP_STDERR=1`

---

## Status and closed tasks

To keep the README focused, the previously long “Open tasks” checklists have been **collapsed into a short “closed/archived tasks” summary**. For ongoing work, see the [Roadmap](#roadmap) and the planning docs under [docs/](docs/).

### Closed / archived tasks (from prior README checklists)

- [x] Document language-server workflows and demo commands (LSP reference + how-to-test snippets).
- [x] Expand Python interop demos (step-by-step `.tiny` programs with expected outputs).
- [x] Evaluate and document the native compiler prototype (smoke tests + limitations).
- [x] Add missing demo commands to [docs/demo_run_commands.md](docs/demo_run_commands.md) (proxy pipeline, Rosetta copy/transpile, try/catch).
- [x] Extend the LLVM emitter baseline (POP support + regression test locking behavior).
- [x] Add LLVM emitter follow-ups (control-flow lowering, frames/calls, string/heap sketch, diagnostics).
- [x] Python↔Tiny bridge layer (allowlists/timeouts + bidirectional demos + tests).
- [x] Rosetta sync improvements (local path support, filters/delays, dry-run, optional transpile trigger).
- [x] CLI env regression for `TINYLANG_COPY_ON_CALL`.

---

## Roadmap

This section remains the *future-looking* plan. Roughly grouped into frontend/language, type discipline, runtime, tooling, and native backends.
For a detailed checklist of open items, see [docs/open_tasks.md](docs/open_tasks.md). The checklist file now exists in the repository and is the canonical place to mark roadmap work as done.

> Note: this repository snapshot is centered on the ImageConverter tooling. If a carried-over roadmap item references TinyLanguage-specific files that are not present in this checkout, `docs/open_tasks.md` now treats that item as archived/not actionable here and records the reason explicitly.

### Frontend / language
- Improve error positions and messages (carry line/column through tokens + AST nodes; unify error type with optional `SourceSpan`).
- Refine the linter (“must-use” across control flow, unreachable-code warnings).

### Type discipline
- No implicit type changes (uniform rules across expressions/functions/heap ops).
- (Optional) simple type inference.

### Runtime
- Harden the heap API (invalid pointer diagnostics, out-of-bounds details, double-delete detection, simple leak tracking).
- Expand the test suite (nested arrays, many `new/delete` pairs, deep recursion, heap failure scenarios).

### Tooling
- CLI wrapper ergonomics and documentation.
- Formatter + lints + stable language-server workflows.

### Native backends
- Keep the C backend stable and documented (see [docs/c_backend.md](docs/c_backend.md)).
- Continue LLVM emission experiments as a separate track.

---

## Glossary

- **FFI (Foreign Function Interface)**: A mechanism that lets code in one language call functions and use data structures from another language, across different runtimes or binary boundaries.
- **IR (Intermediate Representation)**: An internal representation between the AST and a backend output (interpreter execution, native VM bytecode, emitted code). Designed to be simpler than surface syntax and easier to transform/validate.
- **POP**: “Pop from stack.” A VM/bytecode instruction that removes the top value from the evaluation stack (often to discard an unused expression result).
- **Regression test**: A targeted test that ensures a previously fixed bug or behavior does not break again (often a minimal snippet asserting a stable output/error).
- **Smoke test**: A fast end-to-end check that the main pipeline basically works (parse → run → verify a small expected result).
- **TL**: Abbreviation for “TinyLanguage”.
