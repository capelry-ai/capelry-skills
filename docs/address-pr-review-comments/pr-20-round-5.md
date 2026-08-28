# PR 20 review-remediation plan — round 5

Head snapshot: `a9810c60f848c97759af0f056264e3fa6679f60f`.

Three unresolved threads are in scope: strip inline YAML comments before scalar type checks (`PRRT_kwDOSR0Wxs6c5vGo`), validate metadata keys as string scalars (`PRRT_kwDOSR0Wxs6c5vGy`), and reject invalid double-quoted bootstrap escapes (`PRRT_kwDOSR0Wxs6c5vG5`).

Plan: align both dependency-free validators, add focused regressions, run full gates, commit `fix(capelry): close YAML scalar validation gaps`, push to `origin/feat/harness-compatible-skill-installs`, publish after-push evidence replies, wait for CI, resolve all addressed threads, and perform an all-pages closure scan.
