# Local sample library

A fresh database has no library rows, so tile settings and media-type screens have nothing to show. `seed_local_library` fills that gap with a fixed set of sample rows.

The command is for a local checkout. It does not run on startup, in tests, or in the production entrypoint.

## Load it

From the repo root, after migrations:

```bash
uv run --no-sync python src/manage.py seed_local_library
```

Run it again any time. It updates the sample rows in place. It does not add duplicates, and it does not change rows whose `media_id` does not start with `tile-seed-`.

The database file stays in `src/db/` and is not committed. The command is what travels with the repo. On a new worktree or clone: migrate, then run the command.

## Accounts

| Username | Password | Notes |
| --- | --- | --- |
| `demo` | `demodemo` | Built-in demo account. Tiles settings are view-only. |
| `joe` | `localtiles` | Created the first time the command runs. Can save tile settings. |

If `joe` already exists, the password is left alone.

## What you get

Each account gets two rows for movie, anime, manga, game, book, comic, comic issue, board game, and podcast, plus:

- Two TV shows (`Harbor Lights`, `Glass Orchard`), each with season 1 and episodes 1 and 3 marked completed, so show and season progress and last played have a value.
- One music play, `Side A` by Mina Cole on `Room Tone`, with a track number. The artist and album use `tile-seed-` MusicBrainz ids, so they stay separate from real listening history.
- A cast credit, Ada Voss as Night vendor, on both sample movies. That is what the person tile preview uses.

Sample items use source `manual` and media ids such as `tile-seed-movie-2` and `tile-seed-tv-2`. Genres, runtime, progress, score, dates, authors, and synopsis are filled in so each tile field has something to render.

## Where it lives

- `src/users/local_library.py` builds the rows.
- `src/users/management/commands/seed_local_library.py` is the command.
