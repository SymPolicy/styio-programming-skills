# Diagnose a program at this language pin

Always use the observed compiler error; these fragments are not a cross-version diagnostic API.

| Attempt | Pinned diagnostic fragment | Repair direction |
| --- | --- | --- |
| `# identity[T] ...` | `unsupported syntax in authoritative nightly parser` | Remove the authored binder and let an eligible definition infer its relation |
| `identity[i64](1)` | `indexed access requires an indexable value` | Use an ordinary call; add a concrete surrounding annotation only where needed |
| `values := []` with no element context | `empty list literal is underconstrained` | Provide a concrete type such as `values: list[i64] := []` |

The matching complete negative fixtures are [authored binder](../fixtures/upstream/tests/features/inferred_generics/e03_authored_generic_binder.styio), [call-site arguments](../fixtures/upstream/tests/features/inferred_generics/e04_call_site_type_arguments.styio), and [empty list](../fixtures/upstream/tests/features/literal_defaulting/e01_empty_list_without_context.styio). The verifier requires their pinned exit codes (3, 4, 4), expected diagnostic fragments, and no stdout. A signal, crash, timeout, or missing diagnostic is a failure, not an expected rejection.

## Separate source issues from environment issues

- A missing executable or shared library is an environment problem. Record the actual message; do not rewrite the user's source to mask it
- A package hash mismatch means the bundled evidence changed. Restore or review the package before trusting the suite
- A source pin mismatch requires a compatibility check. Passing eleven small fixtures does not establish complete language compatibility
- For input conversion failures, preserve the data that triggered the error and check the annotation boundary; do not silently substitute zero or skip a line
- For file output differences, inspect bytes and separators. `@stdout` and `@file` do not have interchangeable serialization contracts

Shrink a failing example while preserving its input and expected result. Report the final program, exact command, relevant output, and any behavior that was not executed.
