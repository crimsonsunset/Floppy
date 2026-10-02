# Run only tests affected by the diff

Issue [#3](https://github.com/crimsonsunset/Floppy/issues/3). Branch `test/3-run-affected-tests`, cut from `origin/latest` at `c3ff896f`.

## Flow state

| Field | Value |
|---|---|
| Gate | 5 (shipped) |
| Ticket | 3 |
| Branch | test/3-run-affected-tests |
| Repos | floppy (`crimsonsunset/Floppy`) |
| Isolation | worktree |
| Worktrees | /Users/joe/Desktop/Repos/Personal/floppy-wt/3/floppy |
| Base | origin/latest @ c3ff896f |
| QA mode | lets-qa |
| Gates | all |
| Updated | 2026-09-25 |

## Overview

`scripts/test.sh` can run a dotted label you type, or a tag tier. It cannot turn a diff into those labels. This adds one opt-in mode, `--affected`, that does that and hands the labels to the existing `manage.py test` / `ResilientDiscoverRunner` path.

It is the local iteration path. With a coverage map, a pull request runs the tests that executed the changed lines. A push to `latest` still runs the full app list minus `network` and records the next map. The no-arg fast suite stays the pre-finish gate.

This is not a pytest migration and not a package-graph tool.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Change set | Commits since `merge-base(HEAD, origin/latest)`, plus staged, unstaged, and untracked files | Gate 1. A branch-only diff misses the file you are editing. An untracked new test has to be included. |
| Unmapped file under one app | Run that app's label (`app`, `users`, `integrations`, `lists`, `events`, `api`, `config`) | Gate 1. Same apps as `APPS` in `scripts/test.sh`. |
| Templates, static, and other cross-cutting paths | Run the fast suite (no-arg `scripts/test.sh`) | Gate 1. No single app owns `src/templates/` or `src/static/`. |
| Outside the Django runner | `mcp_server/` and `scripts/tests/` are printed and do not escalate | The fast suite never collects them, so running it would not test the change. |
| Flag | `scripts/test.sh --affected`. No-arg behavior unchanged | Existing modes are flags. Replacing the default would change the pre-finish gate. |
| Tag policy | Same as a targeted run: `--exclude-tag network` only | A changed `@tag("slow")` module has to run. Network stays on `--network`. |
| Graph | Direct imports only, plus names re-exported from package `__init__.py` | Tests import `app.models`, not `app.models.media`. A transitive walk through that barrel selects the world. |
| Signals | Modules loaded by string from `AppConfig.ready()`, and music hook files loaded by path, select the app label | The issue says a static graph misses signals. A couple of direct test imports are not the whole set. |
| `@patch` / other strings | Not parsed | The issue says the static graph is enough, and the misses fall back. |
| Escape hatch | `uv.lock`, `pyproject.toml`, `src/manage.py`, `scripts/test.sh`, `src/config/settings.py`, `src/config/test_settings.py`, `src/config/__init__.py`, `src/config/test_runner.py`, `src/config/affected_tests.py` | Issue: lockfile, settings, and runner changes run the fast suite. |
| Non-code | Docs, workflows, images, and other paths outside `src/`, `uv.lock`, and `pyproject.toml` are ignored. If they are the whole diff, run nothing and say so | A README is not an unmapped Python module. |
| Deleted test module | Do not emit a label for a path that is gone | Django errors on a missing label. A deleted source file still selects tests that imported it. |
| CI workflows | A pull request downloads the map from the last successful `latest` run and calls `--affected --include-slow`. `latest` and `release` still run the full app list and upload the map. | The workflow check fails on the PR that edits the workflow. Later PRs do not touch it. No map falls back to the import walk, and a `full` result still runs the CI suite. |
| Code home | `src/config/affected_tests.py` | Sits next to the test runner. Tests import `config.affected_tests` with no path hack. Plain `ast`, no Django import, no new dependency. |

## Scope

In:

- `--affected` on `scripts/test.sh`
- Static import selection, app-label fallback, fast-suite fallback
- One Django test module so CI collects the selector
- A short note in the script usage, `AGENTS.md`, and `docs/architecture/test-suite-cost.md`

Out:

- pytest-testmon, pytest-picked, and the rest of that family. The runner is Django's. Issue #3.
- Switching the suite to pytest so a pytest selector can run it. The runner stays Django's.
- Nx, Turborepo, Bazel. One Django project. Issue #3.
- Parsing `@patch` strings and other lazy references. Issue #3. Empty reverse set already falls back to the app label.
- Making `--affected` the no-arg default. The fast suite stays the gate in `AGENTS.md`.

## Architecture

`scripts/test.sh --affected` calls `PYTHONPATH=src python src/config/affected_tests.py` and branches on one stdout line. The file is executed directly so `config/__init__.py` does not boot Celery. Tests still import `config.affected_tests`.

When `.floppy/affected.coverage` exists, the old side of `git diff -U0 <merge-base>` is intersected with coverage contexts (`dynamic_context = test_function`, `core = ctrace`). Contexts collapse to the test module. The import walk below runs only for paths the map cannot answer, and for a missing map. `scripts/test.sh --affected-record` writes the map from the CI suite.

| First line | What test.sh does |
|---|---|
| `none` | Exit 0. The reason is already on stderr. |
| `full` | The no-arg fast suite (`APPS`, `--exclude-tag slow`, `--exclude-tag network`). |
| `labels` | Following lines are dotted labels. Run them like a targeted invocation: `COMMON` plus `--exclude-tag network`. Extra args after `--affected` pass through. |

Selection, in order. The first matching rule that demands `full` wins over any label set.

1. If any escape-hatch path changed, `full`.
2. If any path is under `src/templates/` or `src/static/`, or is a cross-cutting path that is not under one app and is not in the ignore list, `full`.
3. Otherwise collect labels:
   - A changed `src/<app>/tests/**/test_*.py` that still exists becomes its dotted module.
   - A changed production module selects test modules whose AST shows a direct import of that module, or of a package that re-exports it from `__init__.py`.
   - A changed file under one app with an empty reverse set, and the named signal / hook modules, adds that app label.
4. If the label set is empty and nothing asked for `full`, `none`.
5. `mcp_server/` and `scripts/tests/` never change the mode. They are named on stderr.
6. An app label drops module labels under that same app. The app run already includes them.

Diff command shape:

- `git diff --name-only <merge-base>...HEAD`
- `git diff --name-only HEAD` (staged and unstaged)
- `git ls-files --others --exclude-standard`

`origin/latest` is the base ref. If it is missing, exit non-zero and say so. Do not guess `main`.

## Files

| File | Change |
|---|---|
| [src/config/affected_tests.py](../../src/config/affected_tests.py) | New. Diff to `none` / `full` / labels. |
| [src/config/tests/test_affected_tests.py](../../src/config/tests/test_affected_tests.py) | New. Selector cases, no database. |
| [scripts/test.sh](../../scripts/test.sh) | `--affected` arm and usage lines. |
| [AGENTS.md](../../AGENTS.md) | One Testing bullet for the flag. |
| [docs/architecture/test-suite-cost.md](../architecture/test-suite-cost.md) | Short section: when to use it, and when it gives up and runs the fast suite. |

## Phasing

### Phase 1: Selector

Done.

- `config.affected_tests` with the rules above. Build the reverse map by parsing test modules and package `__init__.py` files under `src/` with `ast`.
- Tests cover: changed test module, source module via a direct import, source module via an `app.models`-style re-export, empty reverse set to an app label, signal module to an app label, template path to `full`, `uv.lock` to `full`, docs-only to `none`, deleted test omitted, untracked test included, `mcp_server/` does not escalate.
- Tests take a file list. They do not shell out to `git` for the cases above. One test can call the git collector against this repo and assert it returns a list.

**Outcome:** `FLOPPY_TEST_FAST_DB=1 scripts/test.sh config.tests.test_affected_tests` passes. The module does not import Django.

### Phase 2: Wire the flag and document it

Done.

- `scripts/test.sh --affected` maps `none` / `full` / `labels` as in the table. Usage comment updated.
- `AGENTS.md` Testing section and `docs/architecture/test-suite-cost.md` name the flag, the change set, and the two fallbacks.

**Outcome:** On a clean tree equal to `origin/latest`, `scripts/test.sh --affected` exits 0 and does not start `manage.py test`. The three docs a person actually reads (`scripts/test.sh` header, `AGENTS.md`, `test-suite-cost.md`) describe the mode.

## Key files

| File | Note |
|---|---|
| [scripts/test.sh](../../scripts/test.sh) | Modes are a `case` on `$1`. Targeted runs exclude `network` only. |
| [src/config/test_runner.py](../../src/config/test_runner.py) | `ResilientDiscoverRunner`. Do not change it. `--parallel` stays serial unless `FLOPPY_TEST_PARALLEL` is set. |
| [src/config/test_settings.py](../../src/config/test_settings.py) | `TEST_RUNNER`, `FLOPPY_TEST_FAST_DB`. |
| [src/app/models/__init__.py](../../src/app/models/__init__.py) | The barrel. Re-export resolution exists because of this file. |
| [src/app/apps.py](../../src/app/apps.py) | `ready()` string-loads the signal modules. |
| [docs/architecture/test-suite-cost.md](../architecture/test-suite-cost.md) | Why "run the suite" is a bad iteration default. Migration floor is ~141s, ~2.8s with `FLOPPY_TEST_FAST_DB=1`. |
| [.github/workflows/lint.yml](../../.github/workflows/lint.yml) | Precedent for a PR diff. Do not edit. |
| [.github/workflows/app-tests.yml](../../.github/workflows/app-tests.yml) | Full job minus `network`. Do not edit. |

## Related

- [#3](https://github.com/crimsonsunset/Floppy/issues/3)
- [Django test labels](https://docs.djangoproject.com/en/5.1/topics/testing/overview/)
- [docs/architecture/test-suite-cost.md](../architecture/test-suite-cost.md)
