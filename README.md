# Styio Programming Skills

Agent skills for writing and verifying end-user Styio programs.

- `styio-programming/` — write, explain, debug, and run `.styio` programs with verified syntax, resource I/O, guards, and inferred callable reuse. For compiler maintenance work use the developer-skills repository instead.
- `tests/` — smoke programs and package checks (`python -m unittest discover tests`; set `STYIO_BIN` for real execution).

Install with the skills CLI:

```sh
npx skills@1.7.0 add SymPolicy/styio-programming-skills --skill styio-programming --agent universal --copy
python .agents/skills/styio-programming/scripts/verify.py --styio-bin "<styio-binary>" --json
```

Without `--styio-bin`, the verifier checks package structure and fixture hashes only.
