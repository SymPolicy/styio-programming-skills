# User recipes

All linked local fixtures are complete upstream programs at the pinned language commit. Some preserve the older `>_(...)` output spelling as source evidence; prefer `expr -> @stdout` for new programs. The verification catalogue records source hashes, input, expected output, and one explicit file-path adaptation.

## First program

```styio
"Hello, World!" -> @stdout
```

Save as `hello.styio`; run `styio --file hello.styio`. Stdout is `Hello, World!` followed by a newline. [Complete fixture](../fixtures/upstream/example/hello_world.styio).

## Standard input → checked numeric transformation → stdout

```styio
# double_it := (x: i64) => x * 2
@stdin >> #(line) => {
  double_it(line) -> @stdout
}
```

Input lines `10`, `20`, `30` produce output lines `20`, `40`, `60`. Preserve `x: i64`: it participates in checked conversion of each input string. Removing the annotation is not necessarily behavior-preserving. [Complete fixture](../fixtures/upstream/tests/features/stdio_input/t05_stdin_transform.styio).

## File transformation

Read [the complete file recipe](../fixtures/upstream/tests/features/stream_processing/t10_full_pipeline.styio). It uses `@file("path") >> #(x) => { ... }` to read items and `result -> @file("path")` to write them. The input `10\n20\n30\n` produces file bytes `204060`, with no inserted separators. A stdout golden must not be reused as a file golden.

The fixture's original output path is `/tmp/styio_doubled.txt`; the verifier changes that one exact path to `doubled.txt` in an isolated directory. When adapting this recipe, choose the user's intended input/output paths explicitly and test actual file bytes.

## Guard chains

These are fragments from [the complete eight-queens program](../fixtures/upstream/tests/features/control_flow/t12_chained_guard_eight_queens.styio):

```styio
?(occupied(cols, col) == 0) =>
    ?(occupied(diag_down, down) == 0) =>
        ?(occupied(diag_up, up) == 0) => {
            next_cols = add_bit(cols, col)
            next_down = add_bit(diag_down, down)
            next_up = add_bit(diag_up, up)
            count += search(row + 1, next_cols, next_down, next_up)
        }
```

The body runs only after all guards pass. The [nested counterpart](../fixtures/upstream/example/algorithms/eight_queens.styio) and this program both print `92`. Retain explicit branching when an intermediate failure needs recovery; do not mechanically flatten arbitrary blocks. Guard chaining does not define a general function-composition operator.

## Inferred callable reuse

```styio
# identity := (value) => value
# relay := (value) => identity(value)
```

The [complete fixture](../fixtures/upstream/tests/features/inferred_generics/t05_generic_composition.styio) uses `relay(42)` and `relay("relay")`, printing both values. Ordinary calls compose the functions. Eligible final, pure definitions infer reusable relations; this does not authorize authored generic parameters or unrestricted polymorphic mutable/captured functions.

## Aligned zip

The [complete zip fixture](../fixtures/upstream/tests/features/stream_processing/t01_zip_collections.styio) pairs `[1, 2, 3]` with `["a", "b", "c"]` using `left >> #(n) & right >> #(s) => { ... }`. It prints `1 a`, `2 b`, `3 c`. Zip stops at the shorter finite source; duplicate external drivers such as `@stdin & @stdin` are not supported. Do not promise longest-input behavior, arbitrary buffering, or asynchronous performance from the syntax.

## Explicit scalar capture

```styio
seed: i64 := 4
# add_seed : i64 $(seed) := (value: i64) => value + seed
```

This fragment is from [the complete scope-isolation fixture](../fixtures/upstream/tests/features/affine_closures/t03_capture_name_scope_isolation.styio). `$(seed)` lists the captured name explicitly; the result type precedes it. The example uses a program-static scalar read, and its full program prints `9` then `5`. Do not extend this example to strings, containers, imported environments, consuming captures, or implicit capture. Mutation and escape have narrower rules; verify a separate supported example before using them.
