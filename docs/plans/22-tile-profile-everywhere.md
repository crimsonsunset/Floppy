# Tile profile everywhere

[Issue #22](https://github.com/crimsonsunset/Floppy/issues/22). Branch `feature/22-tile-profile-everywhere`, cut from `origin/latest` @ `a4b58c58`, then fast-forwarded onto `origin/latest` @ `4f684fb0` before implementation. Follows [11-tile-metadata-settings.md](11-tile-metadata-settings.md), which promised "one profile per media type applies to every tile of that type, on every page."

## Flow state

| Field | Value |
|---|---|
| Gate | 3 (AC met) |
| Ticket | 22 |
| Branch | feature/22-tile-profile-everywhere |
| Repos | floppy |
| Isolation | worktree |
| Worktrees | /Users/joe/Desktop/Repos/Personal/floppy-wt/22/floppy |
| Base | origin/latest @ 4f684fb0 |
| QA mode | browser-qa |
| Gates | all |
| Estimated effort | 2 to 3 days across 4 phases |
| Updated | 2026-10-02 |

## Overview

A type's tile profile (Settings, Tiles) is meant to be the one description of what a tile shows. It is not. `media_card.html` picks the subtitle from an `if/elif` chain, and the profile (`tile_use_lines`) sits second from the bottom. Every older special case is above it and wins, so the same album or episode looks different depending on the page.

Seen on the live site: TV In Progress shows the full TV profile (season and episode, year, genres, status and runtime, score and last played). Music Recently Played shows only a title. The music profile is configured the same way as TV. Movies Recently Played shows the title and a checkmark. The cause is the same in both.

The chain, top to bottom, and where each branch is set:

| Branch | Set by | Added |
|---|---|---|
| `home_music_card` (artist or date text) | Home music album, artist and podcast-show adapters (`home_screen.py`), and `media_list_views.py` | 2026-06-24 |
| `show_episode_identity` (S01E02) | `list` surface (`card_surfaces.py`) | before 2026-09 |
| `use_podcast_show` (show title and percent) | Home podcast rows | before 2026-09 |
| `subtitle_override` / match percent | Discover rows, Home Planning-only filter, Home recently-unrated episode cards | before 2026-09 |
| `show_played_chip` (play count and timestamp) | Home recently-unrated rows | 2026-01-10 |
| `show_next_event_subtitle` | `home` surface | before 2026-09 |
| `tile_use_lines` (the profile) | `card_surfaces._tile_render_context` | 2026-09-29 |
| legacy year and progress | fallback | oldest |

Several hand-rolled grids (library albums and artists, search albums, history, calendar, person cards, statistics highlights) call `{% tile_lines %}` directly and already honor the profile. So the music profile shows on the library page and not on Home.

This change makes the profile win on every card. The older cases stop replacing it. Where one carries information the profile cannot (a next release date, a Discover match percent), it renders as an extra line after the profile lines.

It does not change what the profile can hold, the Tiles settings page, or what any row queries.

## Decisions

Rows marked "owner" were decided in the scoping conversation. Rows marked "call" are judgement calls to review at Gate 2.

| Decision | Choice | Why | By |
|---|---|---|---|
| Rule | The profile always renders. Older cases may add a line after it, never replace it | "I don't want any tiles to be ignored. Music tile is a music tile everywhere." | owner |
| Recently-played chip | Remove it. The profile's Last played field is the timestamp | Asked | owner |
| Profile key for music shelves | `music` for tracks, albums, artists and recent albums. No new key | The registry has no album or artist profile. Home album shells already use `media_type=music` | call |
| Adapters | Home album, artist, recent-album and podcast-show adapters expose the attributes the profile fields read (artist, album, release year, runtime, last played, genres) | The profile renders what the item or adapter has. Today those adapters only carry `card_subtitle_text` | call |
| `home_music_card` | Removed, including the album and artist edit button. That button follows `media.album`, then `media.artist` | A track row that has an album uses the album editor. Chosen at the fidelity pass | owner |
| Episode cards on TV and anime recently-unrated | Use the `episode` profile and drop the forced show/episode string | The `episode` profile already has `show_name` and `episode_code` | call |
| `subtitle_override` on Home Planning-only | Drop it. Release year is a profile field | The override shows the release date only | call |
| Next-event subtitle (Upcoming shelves) | Keep as an extra line after the profile | Upcoming shelves lead with the next release. The profile has no such field | call |
| Discover and hidden | Profile first. Match percent, provenance and hidden-on date follow as extra lines | "No tiles ignored." Untracked candidates only fill the fields they have | call |
| List `S01E02` | Drop the forced line. `episode_code` is a profile field | Same reason | call |
| `uses_line_renderer()` gate | Keep it | It protects a user who never customized a type from a redesign. Out of scope. See Scope | call |
| Test | Template tests for each branch order, plus one Home render test per type that had a bypass | The bypass is in a template, so the check is a rendered page | call |

## Scope

In:

- `media_card.html` subtitle order, and the surface flags in `card_surfaces.py` that feed it.
- Home adapters in `users/home_screen.py` and the matching adapter in `app/media_list_views.py`.
- Removing `show_played_chip` from the card, the row payload, `home_grid.html`, `_scrollable_row.html` and `card_surfaces.py`.
- `docs/architecture/media-card.md`, so the surface table lists the extra lines.

Out:

- Why a recent album reads "Unknown Album" with a placeholder, and why "Refreshing artwork..." never clears. A data and artwork problem, not tile rendering. Tracked in [Issue #23](https://github.com/crimsonsunset/Floppy/issues/23).
- Removing the `uses_line_renderer()` gate. A type the user never customized keeps its legacy markup on purpose. Revisit only if the owner wants fresh accounts to start on profiles.
- A Home row for `episode`. The settings UI lists it, and the `home_screen_row_media_type_valid` constraint does not. Existing behavior, separate from tile rendering.
- Hand-rolled grids that already call `{% tile_lines %}`. They already honor the profile.
- `list_grid.html` (list index tiles). Documented to show item count and completion only.
- Fixing `users.tests.views.test_home_screen`, which errors on `origin/latest` because tests set `video_enabled`. See [PR #21](https://github.com/crimsonsunset/Floppy/pull/21).

## Architecture

`card_surfaces._tile_render_context` already puts `tile_use_lines` and `tile_line_list` on every `{% media_card %}`. The template reads them last. The change moves the profile branch to the top of the `from_grid` subtitle block and turns each older branch into a follow-on:

```
profile lines (tile_use_lines)
  + next-event line         (home surface, media.next_event)
  + match percent / reason  (discover)
  + hidden-on date          (discover_hidden)
```

`home_music_card`, `show_episode_identity`, `use_podcast_show` and `show_played_chip` no longer decide the subtitle. `home_music_card` and `show_played_chip` are gone. The album and artist edit button follows `media.album`, then `media.artist`. `subtitle_override` survives only as the hidden-on date. Discover no longer passes the release date through it.

The profile can only show what the card's object has. Library tracks and TV items already carry it. The Home album, artist, recent-album and podcast-show adapters (`_AlbumHomeAdapter`, `_ArtistHomeAdapter`, `_RecentAlbumAdapter`, `_PodcastShowHomeAdapter`) are thin shells, so they need the attributes `tile_lines()` reads. Phase 2 is that work, and it is the risky part.

## Files

| Path | Change |
|---|---|
| `src/templates/app/components/media_card.html` | Profile branch first. Older branches become follow-on lines. Remove the played-chip block. |
| `src/app/card_surfaces.py` | Drop `show_played_chip` and `show_episode_identity`. Keep `show_next_event_subtitle`. |
| `src/users/home_screen.py` | Adapters carry profile fields. Recently-unrated TV and anime stop setting `subtitle_override`. Planning filter stops setting it. Remove `show_played_chip`. |
| `src/app/media_list_views.py` | Podcast list adapter drops `home_music_card`. |
| `src/templates/app/components/home_grid.html`, `_scrollable_row.html` | Stop passing `show_played_chip`. |
| `src/templates/lists/components/media_grid.html` | Nothing if the flag removal is enough. Check. |
| `src/templates/app/components/discover_row.html`, `discover_row_preview.html`, `discover_rows.html` | Keep the extra lines. Profile renders first. |
| `docs/architecture/media-card.md` | Surface table lists the extra lines. States the rule. |
| `src/app/tests/` and `src/users/tests/` | Branch-order tests and per-type Home render tests. |

## Phasing

### Phase 1: seed and a failing page (about 2 hrs)

- Write the live site's saved tile profiles into the local `dragtest` user in this worktree's database, through `parse_tile_metadata()`. The profiles were read from the site's Tiles page and are the JSON the page holds in `saved`. Music, TV, season, episode, movie, anime and podcast use the multi-line layout. The others keep their defaults.
- Seed one Recently Played item per type, and one music play with a real album, so every bypass has something to render.
- Load Home and record, for each type, which branch won.

**Status:** the template chain on this branch matched the digest above, so the table stands. The seeded Home pass is QA.

**Outcome:** a written table in this doc of type by row by winning branch on the seeded Home, matching the digest above. Any row that disagrees amends the plan.

### Phase 2: the chain and the adapters (about 1 day)

- Move the profile branch to the top of the `from_grid` block in `media_card.html`. Turn next-event, match percent, provenance and hidden date into follow-on lines.
- Remove `show_played_chip` and the `home_music_card` and `show_episode_identity` branches and their callers.
- Give the four Home adapters the attributes the profile fields read. Recently-unrated TV and anime episode cards use the `episode` profile.

**Status:** done. The played-at chip, the forced episode string, and the hardcoded music and podcast subtitle are gone. Adapters carry artist, release date, and genres.

**Outcome:** on the seeded Home, Music Recently Played, Music albums, Music artists, Movies Recently Played, TV Recently Played and a podcast show shelf each show their type's profile lines, and none shows a play-count chip.

### Phase 3: other surfaces (about 4 hrs)

- Discover, Discover hidden, list episodes and the Planning-only shelf render the profile first. Extra lines follow.
- Update `media-card.md` so the surface table lists the extra lines and the rule.

**Status:** done. Discover keeps match percent and provenance under the profile and no longer passes the release date as the subtitle. Hidden cards still pass the hidden-on date, under the profile. `media-card.md` states the rule.

**Outcome:** a Discover card for a movie shows the Movie profile lines and the match percent under them. A list holding a single episode shows the Episode profile with `episode_code`, not a forced `S01E02` line.

### Phase 4: tests and QA (about 4 hrs)

- Template tests for branch order, with and without a profile customized.
- One Home render test for each type that had a bypass.
- Browser QA at 1280 and 390 widths, light and dark, with before and after screenshots of Home, Discover and a list.
- `scripts/test.sh` on the touched labels, `ruff check src`.

**Status:** template order, the album Home card, the episode list card, and ruff are done. Artist, recent-album, and podcast shelves use the same profile path and are not each rendered as their own Home page test. Browser screenshots are QA.

**Outcome:** the Phase 1 table, rerun, shows the profile as the winner for every row. Targeted tests and ruff are clean.

## Key files referenced

| File | Note |
|---|---|
| `src/templates/app/components/media_card.html` | Subtitle chain, lines 459 to 518. |
| `src/app/card_surfaces.py` | Surface flags and `_tile_render_context`. |
| `src/users/tile_metadata.py` | Registry, `uses_line_renderer()`, `tile_lines()`. Genres also read the adapter. |
| `src/app/templatetags/app_tags.py` | `media_type_readable_plural` includes video, so a list page does not crash on that type. |
| `src/users/home_screen.py` | Row builders and the four Home adapters. |
| `src/app/media_list_views.py` | Podcast list adapter exposes the show's genres. It no longer sets `home_music_card`. |
| `docs/architecture/media-card.md` | Surface contract. |
| `docs/plans/11-tile-metadata-settings.md` | The feature this completes. |

## Related documentation

- [Issue #22](https://github.com/crimsonsunset/Floppy/issues/22)
- [Issue #23](https://github.com/crimsonsunset/Floppy/issues/23): Unknown Album and artwork on Music Recently Played.
- [11-tile-metadata-settings.md](11-tile-metadata-settings.md)
- [PR #21](https://github.com/crimsonsunset/Floppy/pull/21): Home Screen drag fix, notes the `video_enabled` baseline errors.
