# Fork catch-up to upstream (Oct 2026)

Bring `crimsonsunset/Floppy` `latest` level with [dannyvfilms/Floppy](https://github.com/dannyvfilms/Floppy) `latest` by taking his side nearly everywhere, then reassess. Prod on Rivendell is the constraint.

## Header

| Field | Value |
|---|---|
| Status | Phases 1–4 done. Phase 5 is waiting on an explicit go. |
| Branch | `chore/31-fork-catch-up-upstream` |
| Base | `upstream/latest` @ `c627799d8` (v26.10.15) |
| Fork tip being replaced | `origin/latest` @ `ede0597a5` |
| Effort | About 1 day, mostly Phase 2 and Phase 5 |
| Updated | 2026-10-16 |

## Flow state

| Field | Value |
|---|---|
| Gate | 3 (stalled on prod cutover) |
| Ticket | 31 |
| Branch | chore/31-fork-catch-up-upstream |
| Repos | floppy |
| Isolation | worktree |
| Worktrees | /Users/joe/Desktop/Repos/Personal/floppy-wt/31/floppy |
| Base | upstream/latest @ c627799d8 |
| QA mode | browser-qa |
| Gates | all |
| Updated | 2026-10-16 |

## Overview

Fork `latest` and `upstream/latest` share history back to `79ec631ac` (2026-10-06). Since then upstream has 272 commits (v26.10.8, v26.10.15, 427 files) and the fork has 85. A content check of those 85 shows almost all are Joe's own PR work, which Danny re-landed under different SHAs, so `git cherry` overstates what is missing. Upstream already has the video type, track detail page, post-listen signal, genres, play links, affected-test selection, Home Screen fixes and `card_metadata` (which replaced the fork's `tile_metadata`).

The fork stays a real deploy source. Joe develops on fork branches and wants them on prod without waiting for Danny. So fork `latest` becomes `upstream/latest` plus one patch (the image name), not a pure mirror.

This plan does not merge upstream into the old fork `latest`, does not hand-port 272 commits, and does not touch feature branches beyond archiving.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Strategy | Reset fork `latest` to `upstream/latest`, force-push with lease | Joe chose "take his". A merge of 427 files would conflict almost everywhere for no gain. |
| Fork patch | Keep `IMAGE_NAME: crimsonsunset/floppy` in `docker-image.yml`, drop `LEGACY_IMAGE_NAME` as the fork already does | Prod pulls `ghcr.io/crimsonsunset/floppy:latest`. Fork branches reach prod without Danny. |
| Upstream PR base | Always `upstream/latest`, never fork `latest` | Keeps the image patch out of PRs to Danny. |
| Data safety | Rehearse the migration on a copy of the latest prod snapshot before any push to `latest` | Prod has 1 user and 12,886 items, 247 of them videos. |
| Archive | Tag old `origin/latest` as `archive/fork-latest-2026-10-06` and keep all branches | A reset loses nothing. Cleanup is deferred by Joe. |
| Leftover PRs | Resubmit every leftover as its own PR from `upstream/latest` | Joe's choice. #1504 is reworked first, see Phase 4. |
| Docs | Retarget `AGENTS.md` and `UPSTREAM_PORTS.md` in a separate small commit | Both still describe `upstream` as `FuzzyGrim/Yamtrack:dev`. |

## Scope

In:

- Archive refs, prod backup, snapshot pull.
- Migration rehearsal against a prod snapshot copy.
- Reset of fork `latest`, image patch, doc retarget.
- Fresh PRs for the leftovers listed in Phase 4.
- Prod cutover with a rollback path.

Out:

- `feature/18-video-surface` (9 WIP commits never merged to `origin/latest`). Joe wants to reassess feature branches after the catch-up. Owner: Joe. Trigger: Phase 5 verified.
- Branch and worktree cleanup (8 local, 26 remote branches already inside upstream, 16 worktrees). Joe chose to leave branches alone this pass. Same trigger.
- The fork `tile_metadata` stack. Superseded by upstream `card_metadata`. Stays only in the archive tag.
- Fork-only plan docs under `docs/plans/`. They stay in the archive tag. This doc is carried onto the new `latest` in Phase 3.
- Any change to upstream's migration files. Reconcile prod, not the graph.

## Architecture

Prod's `django_migrations` is a merged graph. It has the fork-only names (app `0192_music_origin_url`, `0194_merge_20260930_1210`, `0195_merge_20261002_2211`, `0195_video`, `0196_merge_...`, `0197_youtube_video_choices`, `0200_merge_fork_video_and_upstream`; users `0137` to `0151`) and upstream's `app` `0192` to `0199`, including `0197_video`. It lacks upstream's `app` `0200` to `0202`, `users.0149_onboarding_metadata_step`, `integrations` `0058` and `0059`, and `lists.0017`.

After the reset those fork-only names have no file. Django skips applied migrations that are not in the loaded graph, so the extra rows should be harmless. This is the working assumption and Phase 2 tests it. The real risks are:

- Schema drift. Fork `users.0150_remove_tile_metadata` and `0151_reconcile_home_media_and_video_constraints` changed tables that upstream's `users` chain and models also touch.
- Dependencies. Upstream `users.0149_onboarding_metadata_step` must find its parent applied on prod.
- Video. Prod has both `0195_video` and `0197_video` recorded, so `app_video` and `app_videoplay` were created once by one of them. Upstream's model state must match the table.

Rollback is image plus data: the previous image digest `sha256:3e29e734f8e93b749a896b1d0c54f07bd5cec04df71a8c2fb00364bd02bae1bc` and the pre-cutover SQLite snapshot. The entrypoint runs migrations on start, so the backup comes first.

## Files

| Path | Change |
|---|---|
| `.github/workflows/docker-image.yml` | Fork patch: `IMAGE_NAME: crimsonsunset/floppy`, no `LEGACY_IMAGE_NAME`. Fork only, never in an upstream PR. |
| `AGENTS.md` | Branch policy and upstream description retargeted to `dannyvfilms/Floppy:latest`. |
| `UPSTREAM_PORTS.md` | Baselines and "next comparison" retargeted to `upstream/latest`. Record this reset as one ledger outcome. |
| `docs/plans/fork-catch-up-upstream-2026-10.md` | This doc, carried over. |
| `/Users/joe/homelab/stacks/rivendell/docker-compose.floppy.yml` | No change planned. Image stays `ghcr.io/crimsonsunset/floppy:latest`. |

Rehearsal files (scratch worktree, snapshot copy) live outside the repo.

## Phasing

### Phase 1: safety nets (about 30 min)

- Tag `origin/latest` as `archive/fork-latest-2026-10-06` and push the tag.
- On Rivendell, check for auto-update (Watchtower, a pull cron, `restart` plus `pull_policy`). A push to `latest` publishes `ghcr.io/crimsonsunset/floppy:latest`, and an auto-pull would migrate prod before the rehearsal says it is safe. Pin the compose image to the current digest first if anything auto-pulls.
- Check `ps` on Rivendell for stale Floppy or sync jobs before running anything there.
- Copy the newest `/floppy/backups/database/db-*.sqlite3` to `~/floppy-rehearsal/` on the Mac, read-only `scp`. Record its size and `sha256`.

**Outcome:** the archive tag exists on `origin`, prod cannot auto-upgrade, and a snapshot copy with a known checksum sits outside the repo.

### Phase 2: migration rehearsal (about 2 hr)

- Scratch worktree at `upstream/latest` plus the image patch. `SECRET=test-only` plus the snapshot copy as the DB.
- `manage.py migrate --plan`, then `migrate`. Record errors.
- `manage.py makemigrations --check --dry-run` to detect model and schema drift.
- `floppy_preflight` and `check_migration_hygiene --strict`.
- Spot-check counts against prod: 12,886 items, 247 video items, 256 `app_videoplay`, user count 1.
- Open History, Home and a video detail page with the `run-floppy` skill.
- If anything fails, write the smallest repair (a one-off data migration or SQL) and rerun on a fresh copy until clean. Do not edit upstream's migration files.

**Outcome:** met. `migrate` applied `app` `0200`–`0202`, `integrations` `0058`–`0059`, `lists` `0017`, and `users` `0149` on the snapshot copy. `makemigrations --check` reported no changes. Counts were identical before and after (12,799 items: 11,048 episodes, 1,036 music, 399 seasons, 234 videos, 56 shows, 26 movies; 233 `app_video` rows; 243 plays; 1 user). Those are the 02:37 snapshot, not the later live totals. Home, History, and a video detail page returned 200 through Django's test client (`force_login`, `HTTP_HOST=localhost`) because the snapshot user's password is not available for a browser login.

### Phase 3: reset fork `latest` (about 30 min)

- The branch already exists, cut from `upstream/latest` at `c627799d8`. The three commits below land on it.
- Commit 1: image-name patch. Commit 2: this plan doc. Commit 3: `AGENTS.md` and `UPSTREAM_PORTS.md` retarget.
- Force-push to `origin/latest` with `--force-with-lease` against `ede0597a5`. Reset local `latest` to match.
- Watch the fork's `Docker Image` workflow publish the new `latest` tag.

**Outcome:** met. `upstream/latest...origin/latest` is `0 3` at `d55735c0e`. Archive tag `archive/fork-latest-2026-10-06` points at `ede0597a5`. Rivendell has no Watchtower, pull policy, or cron, so the push cannot auto-migrate prod. Lint, migration order, CodeQL, and the merge train passed on that push. App tests and the image publish were still running when this was written.

### Phase 4: leftover PRs (about 3 hr, parallel to Phase 5)

Each is its own branch from `upstream/latest`, so none carries the image patch.

| PR | Source | Note |
|---|---|---|
| Dev server and sample library seeder | [#1502](https://github.com/dannyvfilms/Floppy/pull/1502), `upstream-pr/dev-and-local-library` | Rebase onto `upstream/latest`. Upstream dropped `django-browser-reload` from dev deps, so reconcile `pyproject.toml` and `uv.lock`. Keep `seed_local_library`, `scripts/dev.sh`, `docs/local-sample-library.md`. |
| YouTube history card opens the video | [#1504](https://github.com/dannyvfilms/Floppy/pull/1504), `upstream-pr/history-video-cards` | Rework, do not resubmit as is. Danny rejected it because it opened the Floppy detail page and regressed other chips. Rebuild as a small change that links the stored watch URL and touches only the VIDEO branch of `history_card.html`. |
| Startup import test pins `DEBUG` off | commit `4dea2eb7d` | Small standalone PR for `test_startup_imports`. |
| Origin-URL track play test | `test_music_track_details_lists_play_history_with_origin_url` | Small standalone PR, or fold into the first PR that touches that test file. |

[#1503](https://github.com/dannyvfilms/Floppy/pull/1503) needs no PR. Its search fix is in #1551 and its stats are in #1472.

**Outcome:** met.

- [#1502](https://github.com/dannyvfilms/Floppy/pull/1502) rebased onto `c627799d8` (`33257550b`). `uv lock --check` passed. Ruff passed after sorting the seeder imports.
- [#1595](https://github.com/dannyvfilms/Floppy/pull/1595) links a stored video watch URL and leaves every other card alone. The new template test passed.
- [#1596](https://github.com/dannyvfilms/Floppy/pull/1596) holds both small tests: the `DEBUG=False` pin and the track-page origin URL. #1597 was closed into it after CI failed on a stale sidebar class assertion, which this PR also updates.

### Phase 5: prod cutover (about 1 hr, needs Joe's go)

- Fresh backup: trigger or copy a new snapshot, record its name.
- Pull the new image on Rivendell and `docker compose up -d floppy` from `/Users/joe/homelab/stacks/rivendell`. Run each remote command once and check `ps` before any retry.
- Watch the container log through migrations. Confirm `healthy`.
- Verify against the Phase 2 numbers: item counts, video rows, History, Home, track detail, one scrobble or webhook round trip.
- Rollback if it fails: stop the container, restore the pre-cutover snapshot, pin the old digest.

**Outcome:** `https://track.joe-hassio.com` runs the new image with `showmigrations` showing upstream `app` `0200` to `0202` applied, counts unchanged, and a recorded rollback command that was not needed.

## Key files referenced

| File | Note |
|---|---|
| `UPSTREAM_PORTS.md` | Ledger with Yamtrack-era baseline, retargeted in Phase 3. |
| `AGENTS.md` | Branch policy that still names Yamtrack. |
| `.github/workflows/docker-image.yml` | Triggers on push to `latest`, `release` and tags. Image name is the only fork patch. |
| `src/users/card_metadata.py` | Upstream replacement for fork `tile_metadata`. |
| `src/app/models/video.py` | Upstream video models, must match prod's `app_video` tables. |
| `scripts/dev.sh`, `src/users/local_library.py` | Fork-only dev tooling for #1502. |
| `src/templates/app/components/history_card.html` | Target of the #1504 rework. |
| `/Users/joe/homelab/stacks/rivendell/docker-compose.floppy.yml` | Prod service definition. |

## Related documentation

- [`UPSTREAM_PORTS.md`](../../UPSTREAM_PORTS.md)
- [`docs/agents/migration_sync_playbook.md`](../agents/migration_sync_playbook.md)
- [`docs/local-sample-library.md`](../local-sample-library.md)
- Upstream releases: [v26.10.8](https://github.com/dannyvfilms/Floppy/releases/tag/v26.10.8), [v26.10.15](https://github.com/dannyvfilms/Floppy/releases/tag/v26.10.15)
- Landing PRs for Joe's work: [#1551](https://github.com/dannyvfilms/Floppy/pull/1551), [#1472](https://github.com/dannyvfilms/Floppy/pull/1472), [#1425](https://github.com/dannyvfilms/Floppy/pull/1425), [#1432](https://github.com/dannyvfilms/Floppy/pull/1432), [#1433](https://github.com/dannyvfilms/Floppy/pull/1433), [#1434](https://github.com/dannyvfilms/Floppy/pull/1434), [#1457](https://github.com/dannyvfilms/Floppy/pull/1457)
