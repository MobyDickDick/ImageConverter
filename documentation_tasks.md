# Aufgabenliste: Dokumentationsprüfung aller Sourcecodedateien

Jeder Task: **Ist die jeweilige Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?**

Gesamtanzahl Dateien: **136**

## Erstellung (verwendete Terminal-Commands)

Die Dateiliste wurde per Python-Scan erzeugt:

```bash
python - <<'PY'
import os
exts={'.py','.rs','.c','.cc','.cpp','.h','.hpp','.js','.ts','.jsx','.tsx','.java','.go','.rb','.php','.cs','.swift','.kt','.m','.mm','.scala','.sh','.bat','.ps1','.lua','.pl','.r','.jl','.dart'}
files=[]
for root, dirs, filenames in os.walk('.'):
    for fn in filenames:
        path=os.path.join(root,fn)
        _,ext=os.path.splitext(fn)
        if ext.lower() in exts:
            files.append(path)
files=sorted(files)
output_path='documentation_tasks.md'
with open(output_path,'w',encoding='utf-8') as f:
    f.write('# Aufgabenliste: Dokumentationsprüfung aller Sourcecodedateien\n\n')
    f.write('Jeder Task: **Ist die jeweilige Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?**\n\n')
    f.write(f'Gesamtanzahl Dateien: **{len(files)}**\n\n')
    for path in files:
        f.write(f'- [x] {path}: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?\n')
print(output_path)
PY
```

- [x] ./.vscode/import_code.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./benchmarks/microbenchmarks.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/copy_rosetta_samples.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/factorial/factorial.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/fibonacci/fibonacci.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/fizzbuzz/fizzbuzz.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/hello_world/hello_world.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/python/factorial.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/python/fibonacci.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/python/fizzbuzz.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/python/hello_world.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/python/sorting.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./examples/rosetta/sorting/sorting.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./run_all.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/console_sum.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/formatter.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/language_server.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/language_server_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/native_ir.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/native_python_bytecode.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/native_vm.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/run_all.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/simpelst_Python_program.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/stdlib/__init__.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/stdlib_datetime.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_errors.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_lang_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_api.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_ast.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_codegen_c.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_codegen_llvm.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_codegen_native.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_codegen_py.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_compiler_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_eval.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_highlighting.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_lexer.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_linter.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_parser.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_preamble.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_runtime.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_stitched.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_language_transpilers.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tiny_project_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/tinyc_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./src/transpile_rosetta.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/__init__.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/conftest.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_async_structured.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_async_tokens.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_benchmark_and_fuzz.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_c_codegen.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_cli_smoke.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_concurrency.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_copy_on_call.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_copy_rosetta_samples.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_debug_adapter_flow.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_debugger_hooks.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_error_formatting.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_error_messages.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_errors.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_experimental_math_formula.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_experimental_math_tuples.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_formatter.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_heap_api_errors.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_heap_lints.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_heap_pointer_demo.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_hello_world.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_inheritance.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_language_server.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_language_server_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_llvm_codegen.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_modules.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_namespaces.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_native_backend_errors.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_native_codegen.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_native_ir.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_native_python_bytecode_backend.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_native_vm.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_null.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_number_class.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_number_intervall.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_number_overflow.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_objects.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_operator_overloading.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_pattern_matching.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_python_codegen.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_python_interop_demos.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_readme_concurrency_demo_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_readme_hello_world_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_repl.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_repl_highlighting.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_result_type.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_rosetta_transpile.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_runtime_expansion.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_semantics_suite.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_span_consistency.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_spans.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_src_tiny_regressions.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_stdlib.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_stdlib_sources.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_style_lints.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_tiny_language_cli_self_host.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_tiny_language_compiler_cli_self_host.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_tiny_language_server_cli_self_host.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_tiny_native_backend.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_tiny_project_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_tiny_transpilers.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_transpilers.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_try_catch.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/test_typing.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/detailtests/utils.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_c_backend.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_language_spec_grammar.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_linter_parity.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_llvm_jit.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_src_tiny_regressions.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_standalone_tiny_regressions.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_stdlib_compatibility.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_language.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_language_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_language_compiler_cli.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_language_preamble.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_lexer_self_host.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_parser_self_host.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/test_tiny_wrapper_imports.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tests/utils.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tiny_language.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tools/check_format_lint.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tools/generate_doc_reference.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./tools_unused_scan.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./vscode-extension/extension.js: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./vscode-extension/python/tiny_debug_adapter.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?
- [x] ./vscode-extension/python/vscode_helpers.py: Ist die Sourcecodedatei möglichst vollständig (zeilenweise, mit größeren Zusammenhängen) auf Englisch dokumentiert?

## Zusätzliche Dokumentationsaufgabe

- [x] Gibt es Redundanzen in der Tiny-Language? (siehe `docs/redundancy_review.md`)

## Zusätzliche Aufgabenliste (Projektanforderungen)

- [x] Jede Python-Datei im Projekt wird am Schluss in eine äquivalente Tiny-Datei übersetzt und der Nachweis (Mapping/Tabelle) ist dokumentiert. (siehe `docs/python_to_tiny_mapping.md`)
- [x] Jede Sourcecodedatei ist so detailliert wie sinnvoll dokumentiert (inklusive Kontext/Begründungen für größere Zusammenhänge).
- [x] Große Sourcecodedateien sind in überschaubare, logisch getrennte kleinere Dateien aufgeteilt (inkl. ggf. neuer Modulstruktur und aktualisierten Importpfaden).

## Aufgaben zur Redundanz-Reduktion (aus `docs/redundancy_review.md`)

- [x] Entrypoint-Shims konsolidieren: Migrationsplan definieren, der festlegt, welche Wrapper (`run_all.py`, `tiny_language`, `tiny_language.py`, `src/tiny_lang_cli.py`) entfernt oder umbenannt werden, inklusive Abkündigungszeitraum und kompatibler Übergangskommandos.
- [x] Tooling/Docs anpassen: Dokumentation und interne Tools so aktualisieren, dass sie auf die kanonischen Entry-Points verweisen (z. B. `src/run_all.py`, `src/tiny_language.py`, `src/tiny_language_cli.py`) und die alten Pfade nicht mehr voraussetzen.
- [x] Tests/CI aktualisieren: Prüfen, welche Tests oder Scripts die Wrapper direkt aufrufen, und sie auf die neuen Entry-Points umstellen; Regressionstests ergänzen, die den Migrationsplan validieren.
- [x] Stdlib-Struktur vereinheitlichen: Entscheidungsvorlage erstellen, ob `stdlib/` und `src/stdlib/` zusammengeführt werden können (inkl. Auswirkungen auf Import-Pfade, Runtime-Suche und API-Registrierung).
- [x] Runtime-Suchpfade refaktorisieren: Falls eine Zusammenführung beschlossen wird, Runtime-Logik (`tiny_language_runtime.py`) so anpassen, dass nur ein einziges Stdlib-Root unterstützt wird.
- [x] Übergangsstrategie für Stdlib: Deprecation-Notizen und ggf. Migrationstools bereitstellen, die bestehende Tiny-Programme auf neue Import-Pfade anheben.
