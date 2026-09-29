# Tile metadata settings

[Issue #11](https://github.com/crimsonsunset/Floppy/issues/11). Branch: `feature/11-tile-metadata-settings`, cut from `origin/latest` @ `863d615e`. Follows the "show all metadata on a tile" question after the Recently Played change (`872b0b78`).

## Flow state

| Field | Value |
|---|---|
| Gate | 2 (plan ready) |
| Ticket | 11 |
| Branch | feature/11-tile-metadata-settings |
| Repos | floppy |
| Isolation | worktree |
| Worktrees | /Users/joe/Desktop/Repos/Personal/floppy-wt/11/floppy |
| Base | origin/latest @ 863d615e |
| QA mode | lets-qa |
| Gates | all |
| Estimated effort | 5 to 7 days across 5 phases |
| Updated | 2026-09-29 |

## Overview

Every tile in the app shows a fixed set of metadata. Today the only knob is `media_card_subtitle_display` (`hover` or `always`), which toggles whether the year line is visible. It adds no fields. History tiles show a runtime chip and checkmark, music grids show their own text, and the shared card follows a hard-coded priority chain in `media_card.html`.

This change lets the user pick, per media type, exactly which metadata fields appear under a tile title: all, none, or any subset. One profile per media type applies to every tile of that type, on every page. A new Settings page edits the profiles with a live preview of a real tile.

It is not a per-surface setting, not a new API, and not a redesign of tile layout. Fields render as lines in the existing subtitle stack.

Dependency chain: Phase 1 (registry + storage) blocks everything. Phase 2 (shared card) blocks Phase 3 (the preview renders the shared card). Phases 4 and 5 are independent of Phase 3.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Scope | Every tile: shared card, music grids, history, list tiles, person/cast, stats highlights, active playback, episode rows, calendar rows | Asked for "all tiles around the app". |
| Granularity | One profile per media type, shared by all surfaces | Asked. Removes the per-surface matrix and keeps the page to one editor per type. |
| Person/cast tiles | Own profile key `person` in the same registry | They have no media type. Otherwise they cannot be configured, and "all tiles" would not hold. Assumption, easy to drop. |
| Non-media tiles that show an item | Use that item's media type (stats highlight, active playback, calendar row, episode row uses tv or anime) | No new keys. |
| Layout | Selected fields render as lines in the existing subtitle stack. The title is always shown and is not a field | Asked. Title-less tiles are not usable. |
| Existing prefs | Absorb `media_card_subtitle_display`, `progress_bar`, `hide_zero_rating`. Keep `title_display_preference` and `book_comic_manga_progress_percentage` where they are | See below. |
| Storage | One JSON field on `User` keyed by media type, with a registry module and parser | Matches `detail_page_layouts` / `parse_detail_layouts` in `users/appearance.py` (migration `0132_user_appearance.py`). Per-type keying and a nested option per field fit JSON. Columns would be about 30 booleans per type. A rows model adds a join to every card render. `user` is already in card context, so JSON costs no query. |
| Default profile | Per type, reproduces today's tile output exactly | A user who never opens the page sees no change. |
| Extra-query fields | Selectable everywhere. The Tiles page marks them with an "extra query" pill. A prefetch is added only for surfaces that render a type whose profile enables that field | Asked. Cost is opt-in per user, not paid by default. |
| Settings UI | New Settings page `Tiles` with a per-type editor: check all, check none, per-field checkboxes, and a live preview | Asked. |
| Preview | Server-rendered fragment of the real `{% media_card %}` partial for a sample item of that type from the user's library, re-fetched as the draft changes | One renderer. A client-side mock would drift from the card. |
| API | Web only. The three absorbed prefs keep their names on `/api/v1/user/preferences/`. `PATCH` of a present name writes every type. `GET` returns that name only when every type agrees, and omits it when they differ. `hover` / `always` is a hardcoded choice list after the column drop. Session history reads `hide_zero` from the row's media type | A `GET` that invents a value gets written back and erases per-type edits. `PATCH` already ignores absent keys. |
| Lists index | `list_grid.html` always shows item count and completion. No profile and no hover class. Last-watched stays the sort footer. Items on a list page use the shared card | The index card is not a media tile and has no type to bind `display` to. |
| Surface captions | Stats highlights keep the "Played {date}" line and the top-credit date. Active playback keeps the live clock. Calendar rows keep the media-type label and event time. Each of those templates also renders `{% tile_lines %}` | Those captions are the card's job, not a metadata field. The statistics view test requires the Played date. Chosen 2026-09-29 over dropping them. |

Why two prefs are not absorbed: `title_display_preference` is read by details pages, search, and `Item` (`app/models/item.py`, `media_details_views.py`, `search_views.py`). `book_comic_manga_progress_percentage` is read by track forms, save views, and `Media`. Both change behavior outside tiles, so moving them into a tile profile would change unrelated pages. The Tiles page shows both as linked controls that jump to their Preferences row. Say so in the PR.

How the absorbed three map:

| Old | New |
|---|---|
| `media_card_subtitle_display` (global) | `display` (`hover` or `always`) on each type profile, seeded from the old value |
| `progress_bar` false | `progress` field removed from every type's default field list |
| `hide_zero_rating` | `hide_zero` option on the `rating` field, per type, seeded from the old value |

## Scope

In:

- Field registry, JSON storage, parser, data migration from the three absorbed prefs.
- Shared card (11 surfaces) rendering from the profile, replacing the hard-coded subtitle chain.
- Tiles settings page, per-type editor, all/none/some controls, extra-query pills, live preview.
- Hand-rolled media tiles: music artist and album grids, search inline album cards, search online artist cards, history card, episode row, `media_card_list` row.
- Non-media and secondary tiles: person and cast (live templates only), stats highlight, active playback, calendar list rows and calendar agenda rows.
- `show_media_score` reads `hide_zero` from the item's type profile, including on session history rows.
- API mapping for the three absorbed prefs, OpenAPI regeneration, docs, and a contract test that catches a tile template that ignores the profile.

Out:

- Per-surface overrides. Decision above picked per media type. Add later only if asked.
- A profile for lists-index cards. Item count and completion stay hardcoded and always visible. Last-watched stays a sort footer, same exclusion as the library sort footer.
- `title_display_preference` and `book_comic_manga_progress_percentage`. Used outside tiles, see above.
- Table view columns. `table_column_prefs` already owns them.
- The library sort footer under the card in `media_grid_items.html`. It reports the active sort, it is not tile metadata.
- A new tile-profile API endpoint. Web only, same as Appearance.
- `discover_card.html`. Unused, delete separately.

## Architecture

Registry (`src/users/tile_metadata.py`, new), same shape as `DETAIL_LAYOUT_FAMILIES`:

```python
TILE_FIELDS = {
    "release_year": {"label": "Release year", "types": ALL, "cost": "cheap"},
    "genres":       {"label": "Genres", "types": ALL, "cost": "cheap"},
    "artist":       {"label": "Artist", "types": {"music"}, "cost": "extra_query"},
    # ...
}
```

Initial field list: alt/original title, release year, runtime, genres, user rating, critic rating, status, progress, play count, last played, SxxExx, show/season name, artist, album, track number, author, platform, studio, source/provider, tags, series position, next episode, watch providers, synopsis. Each entry declares the media types it applies to and a cost of `cheap` (on the loaded `Item` or media row) or `extra_query` (needs a join or prefetch). The final cost column is settled in Phase 1 by checking each field against the columns already loaded on each surface. Expected extra-query fields: artist, album, track number, show/season name, tags, next episode, watch providers.

Stored shape on `User.tile_metadata` (JSON, default `{}`):

```json
{"version": 1, "types": {"movie": {"display": "hover", "fields": ["release_year", "rating"], "options": {"rating": {"hide_zero": true}}}}}
```

A missing type falls back to `default_profile(media_type)`, which reproduces the current chain for that type. The parser drops unknown fields and fields that do not apply to the type, so a stale save cannot break a tile.

Rendering: `card_surfaces.card_context` resolves the profile once per card from `user` and `media_type`. When the saved field list matches the type default, `media_card.html` keeps the existing subtitle markup, so an untouched profile renders the same HTML as before. When the list differs, the card loops `{% tile_lines %}` output. Hand-rolled tiles call `{% tile_lines %}`. The `media-card-subtitle-always` class keys off `display`. History shows the status chip only when `status` is enabled and the runtime chip only when `runtime` is enabled. The three surface captions in the decision above stay beside the profile lines.

Prefetch: each surface's queryset builder asks the registry for `extra_query` fields the user's enabled profiles need for the types on that page, and adds the matching `select_related` or `prefetch_related`. A field that is off costs nothing. Same rule as the Recently Played change, where `get_recently_unrated` extends `select_related` for music.

Preview: `GET settings/tiles/preview?type=<type>` with the draft profile in the query string returns the `media_card` fragment for the user's most recently added item of that type. If the user has none, it uses a small fixed sample row for that type so the empty account still sees something. The page refetches that fragment with Alpine `fetch` as the draft changes, the same transport Home Screen uses for its aux calls.

Preferences API, after the columns drop: `UserPreferencesView` special-cases the three names. `PATCH` copies the value onto every type profile (`display`, presence of `progress`, or `options.rating.hide_zero`). `GET` includes the name only when every type currently has that same value. `choices.media_card_subtitle_display` stays `["hover", "always"]` from a constant in the view, because `_field_choices` reads the model field. `show_media_score` takes the item's media type and reads that profile's `hide_zero`.

Home rows are cached and pickled. Field values are computed at render, not stored on cached adapters, so the cache stays valid when a profile changes. The existing pickle regression test stays.

## Files to create / modify

Create:

| Path | Purpose |
|---|---|
| `src/users/tile_metadata.py` | Registry, `default_profile`, `parse_tile_metadata`, per-field value functions. |
| `src/users/migrations/0137_tile_metadata.py` | Add `tile_metadata` JSON, seed from the three prefs. Generated against the current graph. |
| `src/users/migrations/0138_drop_tile_preference_columns.py` | Drop the three absorbed columns and the check constraint after the seed. |
| `src/templates/users/tiles.html` | Tiles settings page and Alpine editor. |
| `src/users/tests/test_tile_metadata.py` | One parser and default-profile check. |

Modify:

| Path | Change |
|---|---|
| `src/users/models.py` | `tile_metadata` field. Drop the three absorbed columns and the `media_card_subtitle_display_valid` constraint in Phase 5. |
| `src/users/urls.py`, `src/users/views.py` | `settings/tiles` and `settings/tiles/preview` routes and views. |
| `src/templates/users/base.html` | Sticky nav entry. |
| `src/templates/users/preferences.html` | Remove the three absorbed rows. Add links to the Tiles page. |
| `src/app/card_surfaces.py` | Resolve the profile in `card_context`. |
| `src/app/templatetags/app_tags.py` | `{% tile_lines %}`, `{% tile_subtitle_class %}`, `{% tile_field_on %}`. `show_media_score` reads `hide_zero` from the movie profile when no type is passed. Templates that know the type use `{% score_is_visible %}`. |
| `src/templates/app/components/media_card.html` | Default field lists keep the old subtitle markup. A custom field list renders the line loop. |
| `src/static/css/input.css`, `main.css` | Rebuild only if new utilities are used. |
| `src/templates/app/components/history_card.html`, `artist_grid_items.html`, `album_list_grid_items.html`, `album_grid.html`, `artist_relation_grid.html`, `app/search.html` (inline albums and online artists), `media_card_list.html`, `episode_row` | Phase 4: call `{% tile_lines %}`. |
| `src/templates/app/components/person_card_inline.html`, `person_filmography_card.html`, `statistics/highlight_set.html`, `active_playback_card.html`, `app/episode_details.html`, `events/components/calendar_list.html`, `events/components/calendar_grid.html` | Phase 5: `{% tile_lines %}`. Highlights, playback, and calendar also keep the captions in the surface-captions decision. `cast_card.html` is unused. Do not wire it. |
| `src/templates/lists/components/list_grid.html` | Phase 5: drop the `media-card-subtitle-always` class. Count and completion stay hardcoded and always visible. |
| `src/app/models/manager.py` and surface queryset builders | Registry-driven prefetch. |
| `src/api/fork_views_users.py` | Map the three absorbed names to the JSON. |
| `src/api/contracts/openapi.yaml` | Regenerate. |
| `docs/architecture/media-card.md` | Add the profile contract and the "which tiles read it" list. |
| `src/app/tests/test_media_card_contract.py` | Extend so a card surface with no profile read fails. |

## Phasing

### Phase 1: Registry, storage, migration

About 1 day.

- Write `tile_metadata.py`: field registry with per-type applicability and cost, `default_profile`, parser.
- Add `User.tile_metadata`. Generate `0137` against the current graph. Data migration seeds `display`, drops `progress` when `progress_bar` is false, and sets `hide_zero` from the old values.
- Run `docs/agents/migration_sync_playbook.md` gates, including `check_migration_hygiene --strict`.
- Default profile per type is checked against the current output of `media_card.html` for that type.

**Outcome:** `parse_tile_metadata({})` returns a valid profile for every media type, `default_profile("movie")` lists the fields the movie tile shows today, and `manage.py migrate` on a copy of the live DB fills `tile_metadata` and changes no rendered tile.

### Phase 2: Shared card renders from the profile

About 1.5 days.

- `card_context` resolves the profile. A custom field list replaces the subtitle chain with the line loop. Special cases (matched title, Recently Played `card_links`, discover overrides, next event, played chip) stay as surface overrides.
- Album library querysets prefetch artist credits only when the music profile enables `artist`. Other surfaces already load the cheap fields.
- `media-card-subtitle-always` keys off `display`. The old preference read is removed from `media_card.html`.
- A saved field list that matches the default keeps today's subtitle markup. A different list renders the line loop.
- Update `test_media_card_contract.py` and the Recently Played pickle test.

**Outcome:** With no saved profile, every shared surface renders the same markup as before (spot check library, home, list, search, discover). Writing `{"types": {"movie": {"fields": ["genres", "runtime"]}}}` to a test user shows genre and runtime lines on a movie tile in library and on home, and no extra queries appear on a page whose profiles enable only cheap fields.

### Phase 3: Tiles settings page with preview

About 1.5 days.

- `settings/tiles` route, nav entry, template extending `users/base.html`, filling `settings_content`.
- Per-type editor: check all, check none, per-field checkboxes, `display` toggle, `hide_zero` option on rating. Extra-query fields carry a pill with a short tooltip.
- Live preview pane fed by `settings/tiles/preview`, refreshed as the draft changes.
- Save posts the same hidden-JSON way the Appearance page does, through `parse_tile_metadata`.
- Remove the three absorbed rows from Preferences and link both non-absorbed prefs from the new page.

**Outcome:** `/settings/tiles` loads, unchecking Genres on the Movie editor removes it from the preview tile immediately, "Check all" turns on every applicable field, "Check none" leaves a title-only tile, and Save persists so the library grid shows the same lines. Extra-query fields show the pill.

### Phase 4: Hand-rolled media tiles

About 1.5 days.

- Music artist and album grids, search inline album cards, search online artist cards, `artist_relation_grid`, history card (runtime chip and checkmark become the `runtime` and `status` fields), `episode_row`, `media_card_list`.
- These templates call `{% tile_lines %}` and drop their own hard-coded subtitle text. History's status and runtime chips follow those fields.
- The album screenshot case (history tile) is the acceptance check.

**Outcome:** On History, Artist, Album, search music results, and the media tiles on a list page, a tile shows exactly the fields set for its media type, matching the Tiles preview, with the runtime chip controllable from the settings page. The lists index is unchanged in this phase.

### Phase 5: Remaining tiles, cleanup, contract

About 1.5 days.

- Person and cast on the live templates (`person_card_inline`, `person_filmography_card`, `episode_details`), stats highlight, active playback, calendar list rows and calendar agenda rows.
- Add the `person` profile editor to the Tiles page.
- `list_grid.html`: remove the subtitle-always class so item count and completion are always visible.
- Drop `media_card_subtitle_display`, `progress_bar`, `hide_zero_rating` and the check constraint in `0138`, after `0137` has seeded the JSON. API `PATCH` fans each present name out to every type. API `GET` omits a name whose types disagree. Types whose default has no `progress` field do not vote on `progress_bar`. `show_media_score` reads the profile. OpenAPI stays `additionalProperties` and was not regenerated.
- Update `docs/architecture/media-card.md`. Extend the contract test so a tile template that does not read the profile fails.
- Run `scripts/test.sh` (fast suite), ruff, `check_migration_hygiene --strict`, and `scripts/replay_upgrade_matrix.sh` for the column drop.

**Outcome:** `rg media_card_subtitle_display src --glob '!**/migrations/**'` only hits the API mapping (`fork_views_users.py` and `tile_metadata.py`). Every media tile in the inventory reads the profile. Lists-index cards show the item count with no hover class. `GET /api/v1/user/preferences/` returns each of the three old names when every type agrees and omits a name when they differ. `PATCH` of one name updates every type and leaves the other names alone. The fast suite and contract tests pass.

## Risks

- The column drop and the API mapping are the only breaking-shaped parts. `GET` omitting a mixed key is a contract change for clients that assume the key is always present. Phase 5 is separable, so Phases 1 to 4 ship with the columns in place if the replay matrix finds trouble.
- Field cost is a guess until Phase 1 checks each field against each surface's loaded columns. A misclassified field either over-warns with the pill or adds a hidden N+1. Phase 2 verifies query counts on the library grid.
- The person profile is an assumption. Cutting it does not affect the other phases.

## Key files

| Path | Note |
|---|---|
| `src/app/card_surfaces.py` | Surface definitions and `card_context`. |
| `src/templates/app/components/media_card.html` | Subtitle priority chain under `from_grid`. |
| `src/app/templatetags/app_tags.py` | `media_card` tag, `hide_zero_rating` read. |
| `src/users/appearance.py` | Registry and parser pattern to copy. |
| `src/users/models.py` | Current pref columns and constraint (about lines 793 to 830, 1516). |
| `src/users/urls.py`, `src/templates/users/base.html` | Settings routes and nav. |
| `src/api/fork_views_users.py` | Preference allowlist. |
| `src/templates/app/components/history_card.html` | The screenshot tile. |
| `src/users/home_screen.py` | Recently Played adapters and `card_links`. |

## Related

- `docs/architecture/media-card.md`
- `docs/agents/migration_sync_playbook.md`
- [Home Screen settings usable](7-home-screen-settings-usable.md)
- [Music track detail page](5-music-track-detail-page.md)
