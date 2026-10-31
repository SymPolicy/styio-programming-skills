# Compatibility and evidence

Skill package version: `0.1.0`. Language guidance is pinned to [Styio source fd3b3e2d9a900fa58bc70641a42885c991650210](https://github.com/Unka-Malloc/styio-nightly/tree/fd3b3e2d9a900fa58bc70641a42885c991650210). No release range is claimed.

`../compatibility.json` stores the machine-readable pin. `../fixtures/cases.json` records eleven complete upstream programs (eight positive and three expected rejections), exact hashes, stdin/goldens, time limits, and the single file-output-path adaptation. All original source bytes are bundled, so package verification needs no compiler checkout or network access.

The recorded Linux test binary was built at `85e41b90c7231b8a263b5b2c88f17fbd5833a078`, a build/routing/tests/docs-only candidate over the language pin. Its SHA-256 is `2b0120e9a066dfdfc9f20cade97fdac5af9953f74e3780bd61952d9874d7c3a0`. These are different commits, not interchangeable labels. The tested setup used GCC 14, LLVM 18.1.8, Release, Tree-sitter enabled, and ICU disabled.

The verifier fingerprints the provided executable and distinguishes `known_tested_binary` from `unverified_binary_provenance`. An unknown binary can pass this finite conformance suite; that does not prove which source built it. `--require-known-binary` makes the recorded fingerprint mandatory. A legitimate independently built binary can have a different machine-specific hash; inspect its provenance and test it instead of equating hash difference with incompatibility.

## What each check means

- Static package pass: required skill files, local reference links, manifest schema, and fixture hashes are valid
- Runtime pass: the supplied binary produced the required results for every selected case; the full default suite is eleven cases
- Agent discoverability: installed `SKILL.md` is in the documented project `.agents/skills/styio-programming` location. This does not prove that a particular agent UI refreshed or selected it
- Platform scope: helper scripts use Python 3.10+ standard library and portable filesystem/process APIs. Linux execution is verified; native macOS/Windows execution is not claimed without testing there

The skill installs no compiler, dependencies, MCP server, credentials, shell settings, or global rules. Obtain a trusted Styio build separately. Run any platform/toolchain setup required by that build before the verifier; it inherits the current process environment without changing it.

For syntax beyond these recipes, consult the pinned [active syntax map](https://github.com/Unka-Malloc/styio-nightly/blob/fd3b3e2d9a900fa58bc70641a42885c991650210/docs/design/syntax/ACTIVE-SYNTAX.md) and verify a minimal program. [The standard-library catalogue](https://github.com/Unka-Malloc/styio-nightly/blob/fd3b3e2d9a900fa58bc70641a42885c991650210/library/README.md) distinguishes active `std.resource` from planned modules.
