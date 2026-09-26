# Home Screen settings usable

[Issue #7](https://github.com/crimsonsunset/Floppy/issues/7). Branch `bugfix/7-home-screen-settings-usable`, cut from `origin/latest` @ `c3ff896f`.

## Flow state

| Field | Value |
|---|---|
| Gate | 3 (AC met, plan reconciled) |
| Ticket | 7 |
| Branch | bugfix/7-home-screen-settings-usable |
| Repos | floppy |
| Isolation | worktree |
| Worktrees | /Users/joe/Desktop/Repos/Personal/floppy-wt/7/floppy |
| Base | origin/latest @ c3ff896f |
| QA mode | browser-qa |
| Gates | all |
| Updated | 2026-09-25 |

## Overview

`/settings/home-screen` is the editor for home rows. Reorder is dead in production because every grip loads SortableJS from jsDelivr, and the live Content Security Policy blocks that origin. The page is also hard to use once a script would load: sections start collapsed with no row titles, desktop hides the row controls until hover, filter text says `In Progress +1`, and unexpanded rows fall back to raw filter keys.

This change makes that settings page readable and makes drag-reorder persist, including the other pages that load the same CDN URL. It does not change the home screen, and it does not change what a library row, list row, or recently-played row queries.

No dependency chain. No Loom.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Sortable source | Commit `sortablejs-1.15.3.min.js` under `src/static/js/libraries/`, same version already pinned | Other third-party JS is a committed file in that directory. `package.json` is Tailwind-only. Production CSP allows `'self'`. |
| Where it loads | One `{% static %}` script in `base.html`, before `savedViews.js` and `collectionCustomFields.js` | Those two modules, the home screen, and the sidebar order script all run on pages that extend `base.html`. A template tag resolves `BASE_URL`. A hardcoded `/static/...` path in a `.js` file does not. |
| CDN strings | Delete every `cdn.jsdelivr.net/npm/sortablejs` assignment | A leftover fallback still violates the CSP. If `Sortable` is missing, keep the existing console warning and do not fetch. |
| List detail script tags | Point `list_detail.html` and `smart_list_detail.html` at the same static file, or drop the tag if the page already gets it from `base.html` | Those two are static `<script src>` tags, not lazy injectors. Do not load the library twice. |
| Closed section header | Show each configured row's serialized `title` on the collapsed media-type bar | `row_title()` already returns the custom name, the list name, or `describe_library_query()`. The header currently prints only `section.label`. |
| Filter button text | Show the human label string from `describe_library_query()`, including on rows with a custom title | `rowFilterLabel()` truncates to `first +N` and calls `fieldOptionLabel()`, which reads `section.filter_fields`. That array is `[]` until expand, so Anime shows `not_caught_up`. |
| `filter_fields` | Stay lazy | `serialize_settings_sections()` documents a full facet scan per type. `test_home_screen_get_omits_filter_fields` locks the omission. Labels do not need that payload. |
| Live edits after expand | Keep the client label helpers once `filter_fields` has loaded | Changing a filter in an open section should update the button without a save. The server string is the pre-expand value. |
| Desktop controls | Remove the `!isDesktop \|\| hovering` gate. Use the existing stacked row layout at every width | Mobile already shows filter, status, sort, and delete. The 40px desktop row is why they were hover-only. |
| Rename field | Default border and a muted placeholder, plus an accessible name | The placeholder is painted with `--color-text`, so it looks like a label. POST still uses the hidden JSON payload. |
| Grip and delete | `aria-label` on both, same idea as `.sidebar-drag-handle` | Icon-only buttons. Chrome flags them. |
| Page intro | One line at the top of this settings page | "These groups are the rows on the home screen. Drag to reorder, click to edit." |

## Scope

In:

- Local Sortable 1.15.3, and every current jsDelivr Sortable URL replaced.
- Home screen settings: collapsed titles, always-visible controls, filter summary text, intro line, rename affordance, grip and delete names.
- Tests that lock the CDN string or the hover-to-open menu path, updated to the new behavior.

Out:

- The home screen render itself. Issue #7 says the editor can stay and the queries stay.
- What a library row, list row, or recently-played row queries. Same reason.
- Adding a Content Security Policy header to `nginx.conf`. The blocking policy is on the live proxy. A same-origin script is what that policy already allows.
- ZXing-style LICENSE, PROVENANCE, and blob-hash locking. That contract exists for the barcode bundle only. Sortable follows htmx and Chart.js: a versioned file in `libraries/`.
- Redesigning sidebar media-type order, list manual order, collection custom fields, or saved views. Those pages only change script origin so their grips work under the same CSP.

## Architecture

Sortable stays a global `Sortable.create` API. Pages that already no-op when `typeof Sortable !== "undefined"` keep that check. Nothing new fetches a URL.

`serialize_settings_sections()` already sends `title`, `custom_title`, and `summary` per row, with `filter_fields: []`. `title` is the custom name when one is set, so it is not always the filter description. Add a `filter_label` on each row set to `describe_library_query(row.filters, user, row.media_type)` for library rows, and to the existing list / recently-unrated summary text otherwise. The filter button renders `filter_label` until the section's `filter_fields` have loaded. After they load, the existing `rowFilterLabel()` path can run, but it joins every label instead of `first +N`.

Collapsed header text is the row `title` values for that section, in order. Expanding still reveals the editor.

`x-show="!isDesktop || hovering || openMenu !== null || row.editorOpen"` is gone. The narrow-width row rules in `input.css` apply at every width, and the same block in `main.css` was edited to match. No new utility classes, so the Tailwind build was not regenerated.

## Files

| Path | Change |
|---|---|
| `src/static/js/libraries/sortablejs-1.15.3.min.js` | New. Upstream 1.15.3 min build. |
| `src/templates/base.html` | Script tag for that file, before `{% block js %}`. |
| `src/templates/base_public.html` | Same tag. Public list pages extend this template, not `base.html`. |
| `src/static/js/savedViews.js` | Drop `SORTABLE_URL`. No network fetch. |
| `src/static/js/collectionCustomFields.js` | Drop the CDN `script.src`. |
| `src/templates/users/home_screen.html` | Drop the CDN `script.src`. Collapsed titles, visible controls, filter label, intro, rename affordance, aria-labels. |
| `src/templates/users/components/_media_type_order_js.html` | Drop the CDN `script.src`. |
| `src/templates/lists/list_detail.html` | CDN tag removed. The base template already loaded the library. |
| `src/templates/lists/smart_list_detail.html` | Same. |
| `src/users/home_screen.py` | `filter_label` on each serialized settings row. |
| `src/static/css/input.css` | Row controls visible without hover. |
| `src/static/css/main.css` | Same custom rules as `input.css`. Edited in place. No new Tailwind utilities. |
| `src/users/tests/views/test_home_screen.py` | CDN assertion, `filter_label`, collapsed title markup. |
| `src/users/tests/views/test_home_screen_menus.py` | Menus open without `row.hover()`. |

## Phasing

### Phase 1: Local Sortable

About half a day.

- Download Sortable 1.15.3 min into `src/static/js/libraries/sortablejs-1.15.3.min.js`.
- Load it from `base.html` with `{% static %}`.
- Remove the jsDelivr URL from the six other call sites. Leave the "already loaded" short-circuit and the existing unavailable warning.
- Update `test_home_screen.py`, which currently asserts the home screen HTML has no static `src="…Sortable.min.js"` because the URL lived only inside Alpine.

**Outcome:** `rg cdn.jsdelivr.net/npm/sortablejs src` is empty. A rendered page that extends `base.html` includes `/static/js/libraries/sortablejs-1.15.3.min.js`. `scripts/test.sh users.tests.views.test_home_screen` passes.

### Phase 2: Settings page you can read

About a day.

- Intro line on the home screen settings page.
- Collapsed section shows configured row titles.
- `filter_label` from `describe_library_query` on the serialized row. Filter control shows that string before `filter_fields` loads, and the full joined labels after.
- Delete the desktop hover gate. Stack the controls the way the narrow layout already does. Regenerate `main.css`.
- Visible input border, muted placeholder, accessible name on the rename field. `aria-label` on the section grip, the row grip, and delete.
- Point `test_home_screen_menus.py` at visible controls. Do not require hover. Wait for the `filter-fields` response before keyboard focus. Expanding a section replaces the row DOM when that payload arrives, and a focus call during that swap lands on the section header.

**Outcome:** With TV Shows collapsed, the header lists that section's row titles in human language (`In Progress • Not Caught Up`, not `not_caught_up`). Filter, status, sort, and delete are in the accessibility tree without a hover. `scripts/test.sh users.tests.views.test_home_screen` passes. The Playwright file is updated. It stays `@tag("slow", "playwright")` and is not part of the fast suite.

After both phases, reconcile this doc with what shipped (`update-planning-md`). That pass is flow bookkeeping, not a third implementation phase.

## Key files

| Path | Note |
|---|---|
| `src/templates/users/home_screen.html` | Alpine `homeScreenSettings()`, `ensureSortable`, `rowFilterLabel` `+N` truncation, hover `x-show`. |
| `src/users/home_screen.py` | `serialize_settings_sections`, `describe_library_query`, `row_title`, `row_summary`. `filter_fields` omitted on purpose. |
| `src/users/views.py` | `home_screen` GET/POST and `home_screen_filter_fields`. |
| `src/static/css/input.css` | `.home-settings-row-*` responsive rules. |
| `src/templates/users/components/media_type_picker.html` | Existing reorder `aria-label` to copy. |
| `src/app/tests/test_static_libraries.py` | ZXing vendoring contract. Not the pattern for this file. |
| `nginx.conf` | Serves `/static/`. No CSP header in repo. |

## Related

- [Issue #7](https://github.com/crimsonsunset/Floppy/issues/7)
- `docs/architecture/theming.md` for the color tokens the rename field already uses
