---
name: styio-programming
description: Write, explain, debug, and run end-user Styio programs with verified syntax, resource I/O, guards, and inferred callable reuse. Use for .styio programs, not compiler implementation or maintenance.
---

# Styio Programming

Help the user produce a small, runnable Styio program and verify its observable result. This skill targets language commit `fd3b3e2d9a900fa58bc70641a42885c991650210`; [compatibility](references/compatibility.md) distinguishes that source pin from the tested build. Do not silently change the user's compiler version.

## Write and verify

1. Identify inputs, expected outputs, the user's compiler path, and any file effects. Prefer an existing project convention when it agrees with the pinned syntax.
2. Read only the relevant recipe in [idioms](references/idioms.md). Use the bundled complete fixtures as executable evidence; excerpts marked as fragments need their surrounding program.
3. Write the smallest suitable `.styio` program. Prefer `expr -> @stdout`, ordinary callable composition, and explicit resource flow. Keep necessary type annotations at input/conversion boundaries.
4. Run the compiler as `"<styio-binary>" --file program.styio`, supplying representative input. Use a temporary working directory for file-output tests. Compare exact output bytes, including newlines. Do not treat parse-only success as a working program.
5. If execution fails, inspect the actual diagnostic and consult [diagnostics](references/diagnostics.md). Make a scoped repair and rerun the same case plus relevant edges. If the compiler is unavailable, label the result unexecuted and explain the missing prerequisite.

For setup checks, run `python "<this-skill>/scripts/verify.py" --styio-bin "<styio-binary>" --json`. Without `--styio-bin`, this validates package structure and fixture hashes only; runtime remains `not_run`. The verifier does not install anything or infer source provenance from a version string.

## Syntax decisions that matter

- `name := expr` prevents rebinding; it does not make container elements immutable. `name = expr` is mutable binding/rebinding
- `# identity := (value) => value` is a callable definition; use `identity(x)` for a call and `<| expr` for a return from a block
- `?(condition) => { ... } | { ... }` is branching. Consecutive guards are useful when no intermediate else action is needed
- `source >> #(item) => { ... }` iterates items; `value <- @stdin: i64` is a typed pull; `expr -> @stdout` writes a sink. These are distinct operations
- `[0..7]` includes both endpoints. For aligned iteration use the zip recipe; it stops at the shorter finite input
- Empty `[]` needs element-type context. Reusable callable types may be inferred, but authored `[T]` binders and call-site `[i64]` specialization are rejected
- Use explicit `$(name)` only within the supported capture recipe. Do not assume arbitrary implicit closures or container capture
- Only `std.resource` has active standard-library evidence at this pin. Do not invent `map`, `filter`, `reduce`, package managers, or imports from planned `std.*` modules

Prefer a clear explicit program over speculative syntax or a shorter expression. Check unverified behavior against the pinned [active syntax map](https://github.com/Unka-Malloc/styio-nightly/blob/fd3b3e2d9a900fa58bc70641a42885c991650210/docs/design/syntax/ACTIVE-SYNTAX.md) and test it, rather than presenting analogy with another language as evidence.
