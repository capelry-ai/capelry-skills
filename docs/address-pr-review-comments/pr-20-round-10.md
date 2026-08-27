# PR 20 review-remediation plan — round 10

PR #20 exact initial head: `8acb124c6292185f90394dac4b7aaa42e49fdd43`. Initial scan: 26 threads, 24 resolved/excluded, two unresolved, no pagination remainder. Push target: `origin HEAD:refs/heads/feat/harness-compatible-skill-installs` (normal/non-force).

- `PRRT_kwDOSR0Wxs6c91Ee`: normalize every YAML line-break character (CR/LF, NEL U+0085, LS U+2028, PS U+2029) before frontmatter scanning in both validators; verify the reviewer sequence fixture fails and forced replacements preserve the destination.
- `PRRT_kwDOSR0Wxs6c91Ej`: extend the shared non-string plain-scalar grammar to YAML 1.1 sexagesimal integers/floats in both validators; cover required/optional/metadata cases and rollback.

Keep all 68 prior regression tests. Run focused tests, full suite, py_compile, Ruff, built-in/official validation, PyYAML comparison, and diff hygiene. Commit, push, verify exact PR head, then post replies (after push per user ordering), await CI, resolve after state rechecks, update PR evidence, and perform an all-pages closure scan.
