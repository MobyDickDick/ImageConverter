# Reserved real composition candidates, not conversion acceptance

Two families are marked from original JPEG pixels and reserved **before any
converter trial or production edit**: HC0010 (nine shaded radiator elements,
two occluded connectors) and Rail (five chamfered holes in textured metal).
Each family includes all known filenames and future transformed descendants.
There are **zero conversion trials**, and acceptance is **unknown**, not 0/2
or 2/2. The production `src/` snapshot remains identical to `147e86405`.

`freeze/manifest.json` seals original bytes, lossless decoded RGB pixels,
descriptions, visible object bounds, relations, source audit and runtime hashes.
The independent markers were drawn by the implementing agent from enlarged
original pixels without detector proposals or SVGs. No independent human
annotation audit has taken place. The historical catalogue may have exposed
these images to earlier batches; this is not a claim of pristine provenance.

Both candidates extend beyond the present gradient-circle scene contract.
HC0010 has eleven required objects and clipped outer elements. Rail has
chamfered holes, texture, a dark groove and lower ridges. The existing native
circle/rectangle checker cannot fully validate these requirements. The six
explicit `acceptance_gaps` must be covered by an independent oracle before the
first trial; neither candidate can presently establish positive transfer of
the existing primitive grammar. This reserve does not close
SEARCH-STRUCTURE-01, GENERAL-SCENE-COMPOSITION-09 or GENERAL-SCENE-REAL-05.

The pinned source/history search found no HC0010 token in `src`, `tests`,
`tools`, `config` or `docs`. Rail matched two ordinary English comments in the
zigzag-panel implementation and two historical panel commits (`7ab31d915`,
`17178082f`), inspected as unrelated to Rail.jpg. Literal-name search cannot
exclude unnamed relatives or every past batch. Previously developed panels,
GE0018/GE0307 and related Nordic flags were excluded from this reserve.

The standard real-scene preparer rejects `sealed_unrun` annotations before
creating an output directory. Deliberate release requires a fixed development
runtime, complete independent checks for all gaps, and predeclared budgets
and gates. Do not tune on the first results. After exposure, the entire family
becomes development; a later claim needs different reserved families.

Read-only verification, which never imports or invokes the converter:

```powershell
.venv/Scripts/python.exe -m tools.freeze_real_composition_holdouts --verify artifacts/evaluation/real_composition_holdout_freeze_v1/freeze/manifest.json --check-current-runtime
```

Omit `--check-current-runtime` when checking historical evidence after future
runtime development. A new snapshot requires a **new** destination:

```powershell
.venv/Scripts/python.exe -m tools.freeze_real_composition_holdouts --freeze .tmp/new-real-family-freeze
```

`checks.json` records the exact final commands, exit codes and JUnit hashes.
55 targeted/evidence tests and the separate 42-test core profile pass. These
are preparation/integrity regressions, not conversion-quality measurements.
The full standard suite and archive reconversion were not run.

See [work package and remaining scope](../../../docs/next_arbeitspaket_2026-11-03_real_family_freeze.md).
