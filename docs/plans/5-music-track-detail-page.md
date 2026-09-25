# Track detail page

[Issue #5](https://github.com/crimsonsunset/Floppy/issues/5). A track is a row on the album. This adds the page artist and album already have.

## Flow state

| Field | Value |
|---|---|
| Gate | 4 (QA pass) |
| Ticket | #5 |
| Branch | feature/5-music-track-detail-page |
| Repos | floppy |
| Isolation | worktree |
| Worktrees | /Users/joe/Desktop/Repos/Personal/floppy-wt/5/floppy |
| Base | origin/latest @ c3ff896f |
| QA mode | lets-qa |
| Gates | all |
| Updated | 2026-09-25 |

## Overview

Artist and album pages are `media_details.html` with `music_detail_kind` of `artist` or `album`. A track gets the same shell, nested under its album.

The page shows the track title, a link to the artist, a link to the album, genre chips, and that track's play history. Genre fill stays where it is. SoundCloud enrichment and the MusicBrainz fallback are not part of this change.

`fix/music-genres` is a parallel line. The genre commits are already on `latest` under different hashes. Cut from `origin/latest`.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| URL | `/details/music/artist/<artist_id>/<artist_slug>/album/<album_id>/<album_slug>/track/<track_id>/<track_slug>/` | Same shape as the album URL. Ids look the row up. Slugs are cosmetic, via `_music_slug`. |
| Short redirect | `music/track/<track_id>/` redirects to the canonical path | Artist and album already have `music/artist/<id>/` and `music/album/<id>/`. |
| Mismatch | Wrong artist id, or a track whose album is not the album in the path, redirects to the canonical track URL | Album details already redirect when `artist_id` does not match the album. |
| Shell | `music_detail_kind == "track"` and a track component included from `media_details.html` | The issue asks for the same kind of page artist and album already are. Episode details are a different shell. |
| Genres | `Track.genres` when that list is non-empty, otherwise `album.genres` | Locked in Gate 1. Chips use the existing sidebar markup (`--color-genre-badge-*`). No new chip design, no shared partial. |
| Plays | The same `Music` resolution the album row uses: this user's row for `track_id`, else the recording id | One track page should not invent a second way to find listens. History is `music.history` ordered by `-end_date`. Rows with no `end_date` are omitted. |
| Origin URL | Each history row links `origin_url` when that value is `http://` or `https://` | The field already lives on `Music` and `HistoricalMusic`. Anything else stays off the page so the href cannot be a script URL. |
| No plays | The page still renders. History is empty. | The row on the album exists before anyone has listened. |
| Entry | The album track title becomes a link. Statistics, media cards, and the API stay on the album URL. | The page has to be reachable from the row the issue describes. Retargeting the rest of the app is a different change. |

## Scope

In:

- Canonical track route, view, template branch, and `music_track_url`.
- Short `music/track/<id>/` redirect.
- Sidebar genre chips with the track-then-album rule.
- On-page play history for that track, including origin URL when stored.
- Album track title links to the track page.
- Tests next to the existing artist/album contract tests.
- A short note in `docs/agents/music_integration.md` for the new URL. That doc still describes the legacy templates. This change does not rewrite it.

Out:

- Genre fill, SoundCloud enrichment, MusicBrainz genre fallback. Issue #5 says those stay as they are.
- A shared genre-chip partial. Artist, album, and podcast already copy the markup. A fourth copy matches that. Extracting it is a cleanup with no ticket.
- Cross-album history for one MusicBrainz recording id. The page is this `Track` row, same as the album list.
- Pointing statistics, library cards, or API track payloads at the track URL. No ticket for that. The album row is the entry.

## Architecture

Catalog metadata is `Track` (`album` FK, `title`, `genres`, duration, disc and track number, `musicbrainz_recording_id`). Per-user listens are `Music` rows. Play history is django-simple-history on `Media`, not a separate Play model. `origin_url` is on `Music` and `HistoricalMusic`.

The album renderer already builds `{track, music, history, collection_entry}` per row. The track view loads one track and reuses that resolution for the signed-in user. It does not scrobble or populate the album. When the user has no listen, it looks the recording up on MusicBrainz (`recording` when the track has an id, otherwise a title search) and shows that payload: release date, runtime when the track has no duration, cover when the album has none, and genres when the track and album have none. Artist and album stay the header links. The response is not written back.

Genre list for the template:

1. `track.genres` if it has any entries.
2. Else `album.genres`.
3. Else, when there is no listen, the MusicBrainz recording's genres.
4. Else no chips.

Empty string entries do not count as a genre.

## Files

| File | Change |
|---|---|
| `src/app/urls.py` | Canonical track route and `music/track/<id>/` redirect |
| `src/app/music_views.py` | Track renderer: lookup, redirects, genre list, history |
| `src/app/views.py` | Re-export the view the way artist and album are re-exported |
| `src/app/templatetags/app_tags.py` | `music_track_url` |
| `src/templates/app/media_details.html` | Branch for `music_detail_kind == "track"` |
| `src/templates/app/components/detail_music_track.html` | New. Title, artist (album credits when the album has them, otherwise the album artist), album link, track number, duration, genre chips, history |
| `src/templates/app/components/detail_music_album.html` | Track title links to the track page |
| `src/app/tests/views/test_media_details.py` | Page, redirect, genres, history |
| `src/app/tests/test_templatetags.py` | Canonical track URL shape |
| `docs/agents/music_integration.md` | Note the track URL. Do not rewrite the doc |

## Phasing

### Phase 1: URL and shell

About half a day.

- Register the nested route and the short redirect.
- Render the shared media details shell with the track title, artist link, and album link.
- Redirect when the artist id or album id in the path does not belong to that track.
- Tests for resolve, redirect, and the three labels.

**Outcome:** `GET` of the nested URL returns the media details shell with the track title, a link to the artist, and a link to the album. A wrong artist or album id in the path redirects to the canonical track URL. `music/track/<id>/` lands on that same URL.

### Phase 2: Genres, history, album link

About half a day.

- Sidebar chips from `Track.genres`, falling back to `album.genres`.
- List this track's completed listens, newest `end_date` first. A row with no `end_date` is skipped. `origin_url` is a link only when it is `http://` or `https://`.
- A track with no `Music` row still renders, with no listen rows.
- The album page track title links here.
- Tests for track genres, album fallback, empty history, a history row with an origin URL, and the album-row href.
- One paragraph in `docs/agents/music_integration.md` for the track URL.

**Outcome:** A track with its own genres shows those chips. A track with none shows the album's. The page lists that track's listens. The album track title is a link to this page. Genre fill code is unchanged.

## Key files

| File | Note |
|---|---|
| `src/app/music_views.py` | Artist and album renderers, album track `Music` map, history order |
| `src/app/urls.py` | Canonical `details/music/...` routes and legacy redirects |
| `src/templates/app/media_details.html` | Dispatches on `music_detail_kind` |
| `src/templates/app/components/detail_music_album.html` | Album sidebar genres and the track list |
| `src/templates/app/components/fill_track_song.html` | Existing "Previous Listens" list the page history should resemble |
| `src/app/models/music.py` | `Track`, `Music`, `origin_url` |
| `src/app/templatetags/app_tags.py` | `music_artist_url`, `music_album_url`, `_music_slug` |
| `docs/agents/music_integration.md` | Data model. URL section is stale |

## Related

- [Issue #5](https://github.com/crimsonsunset/Floppy/issues/5)
- `docs/agents/music_integration.md`
- After the code matches this doc, reconcile it with `update-planning-md` (status, file list, phase text). That pass is the close-out, not a third implementation phase.

## Close-out

Implementation is `a4aad62c`. This pass recorded the sidebar track number and duration, album-credit artist line, skipped history rows with no `end_date`, and http(s)-only origin links. Genre fill was not touched.
