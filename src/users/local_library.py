"""Sample library for local tile and media-type checks.

Rows are keyed by ``tile-seed-*`` media ids. Running this twice updates those
rows and does not touch anything else in the database.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone

from app.models.choices import MediaTypes, Sources, Status
from app.models.item import Item
from users.demo import ensure_demo_user

LOCAL_USERNAME = "joe"
LOCAL_PASSWORD = "localtiles"  # noqa: S105
LOCAL_EMAIL = "joe@example.com"
RELEASE = datetime(2024, 3, 12, 12, tzinfo=UTC)
SEED = "tile-seed"

_TRACKED = (
    {
        "media_type": MediaTypes.MOVIE.value,
        "model": "Movie",
        "media_id": f"{SEED}-movie-1",
        "title": "The Copper Lantern",
        "genres": ["Drama", "Thriller"],
        "runtime": 112,
        "progress": 1,
        "status": Status.COMPLETED.value,
    },
    {
        "media_type": MediaTypes.MOVIE.value,
        "model": "Movie",
        "media_id": f"{SEED}-movie-2",
        "title": "Night Market",
        "genres": ["Drama", "Thriller"],
        "runtime": 118,
        "progress": 1,
        "status": Status.COMPLETED.value,
    },
    {
        "media_type": MediaTypes.ANIME.value,
        "model": "Anime",
        "media_id": f"{SEED}-anime-1",
        "title": "Paper Crane",
        "genres": ["Animation", "Science Fiction"],
        "runtime": 24,
        "progress": 8,
    },
    {
        "media_type": MediaTypes.ANIME.value,
        "model": "Anime",
        "media_id": f"{SEED}-anime-2",
        "title": "Signal Drift",
        "genres": ["Animation", "Science Fiction"],
        "runtime": 24,
        "progress": 12,
    },
    {
        "media_type": MediaTypes.MANGA.value,
        "model": "Manga",
        "media_id": f"{SEED}-manga-1",
        "title": "Ink District",
        "genres": ["Fantasy", "Adventure"],
        "runtime": 22,
        "progress": 20,
        "authors": ["Kenji Arai"],
    },
    {
        "media_type": MediaTypes.MANGA.value,
        "model": "Manga",
        "media_id": f"{SEED}-manga-2",
        "title": "Low Tide",
        "genres": ["Fantasy", "Adventure"],
        "runtime": 22,
        "progress": 42,
        "authors": ["Kenji Arai"],
    },
    {
        "media_type": MediaTypes.GAME.value,
        "model": "Game",
        "media_id": f"{SEED}-game-1",
        "title": "Dockyard",
        "genres": ["Adventure", "Indie"],
        "runtime": 90,
        "progress": 600,
    },
    {
        "media_type": MediaTypes.GAME.value,
        "model": "Game",
        "media_id": f"{SEED}-game-2",
        "title": "Relay",
        "genres": ["Adventure", "Indie"],
        "runtime": 90,
        "progress": 840,
    },
    {
        "media_type": MediaTypes.BOOK.value,
        "model": "Book",
        "media_id": f"{SEED}-book-1",
        "title": "The Quiet Index",
        "genres": ["Fiction", "Mystery"],
        "runtime": 390,
        "progress": 120,
        "authors": ["Ada Voss"],
        "series_position": 2,
        "number_of_pages": 280,
    },
    {
        "media_type": MediaTypes.BOOK.value,
        "model": "Book",
        "media_id": f"{SEED}-book-2",
        "title": "Salt Grammar",
        "genres": ["Fiction", "Mystery"],
        "runtime": 412,
        "progress": 180,
        "authors": ["Ada Voss"],
        "series_position": 3,
        "number_of_pages": 320,
    },
    {
        "media_type": MediaTypes.COMIC.value,
        "model": "Comic",
        "media_id": f"{SEED}-comic-1",
        "title": "Red Margin",
        "genres": ["Superhero", "Action"],
        "runtime": 28,
        "progress": 4,
        "authors": ["Nora Pell"],
    },
    {
        "media_type": MediaTypes.COMIC.value,
        "model": "Comic",
        "media_id": f"{SEED}-comic-2",
        "title": "Folded City",
        "genres": ["Superhero", "Action"],
        "runtime": 28,
        "progress": 6,
        "authors": ["Nora Pell"],
    },
    {
        "media_type": MediaTypes.COMIC_ISSUE.value,
        "model": "ComicIssue",
        "media_id": f"{SEED}-comicissue-1",
        "title": "Red Margin #1",
        "genres": ["Superhero", "Action"],
        "runtime": 24,
        "progress": 1,
        "authors": ["Nora Pell"],
    },
    {
        "media_type": MediaTypes.COMIC_ISSUE.value,
        "model": "ComicIssue",
        "media_id": f"{SEED}-comicissue-2",
        "title": "Folded City #4",
        "genres": ["Superhero", "Action"],
        "runtime": 24,
        "progress": 1,
        "authors": ["Nora Pell"],
    },
    {
        "media_type": MediaTypes.BOARDGAME.value,
        "model": "BoardGame",
        "media_id": f"{SEED}-boardgame-1",
        "title": "Harbor Route",
        "genres": ["Strategy", "Family"],
        "runtime": 60,
        "progress": 3,
    },
    {
        "media_type": MediaTypes.BOARDGAME.value,
        "model": "BoardGame",
        "media_id": f"{SEED}-boardgame-2",
        "title": "Nine Tokens",
        "genres": ["Strategy", "Family"],
        "runtime": 75,
        "progress": 5,
    },
    {
        "media_type": MediaTypes.PODCAST.value,
        "model": "Podcast",
        "media_id": f"{SEED}-podcast-1",
        "title": "Side Channel",
        "genres": ["Society", "Interview"],
        "runtime": 38,
        "progress": 20,
    },
    {
        "media_type": MediaTypes.PODCAST.value,
        "model": "Podcast",
        "media_id": f"{SEED}-podcast-2",
        "title": "Late Shift",
        "genres": ["Society", "Interview"],
        "runtime": 46,
        "progress": 28,
    },
)

_SHOWS = (
    {"media_id": f"{SEED}-tv-1", "title": "Harbor Lights"},
    {"media_id": f"{SEED}-tv-2", "title": "Glass Orchard"},
)


def seed_local_library():
    """Upsert the sample library for the demo account and ``joe``.

    Returns the number of sample items touched.
    """
    users = [ensure_demo_user(), _ensure_local_user()]
    played = timezone.now() - timedelta(days=3)
    touched = 0
    for user in users:
        for row in _TRACKED:
            _seed_tracked(user, row, played)
            touched += 1
        for show in _SHOWS:
            _seed_show(user, show, played)
            touched += 1
        _seed_music(user, played)
        touched += 1
    _seed_cast()
    return touched


def _ensure_local_user():
    """Return the local ``joe`` account, creating it on a fresh database."""
    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(
        username=LOCAL_USERNAME,
        defaults={
            "email": LOCAL_EMAIL,
            "is_active": True,
            "is_demo": False,
            "is_staff": False,
            "is_superuser": False,
        },
    )
    if created:
        user.set_password(LOCAL_PASSWORD)
        user.save(update_fields=["password"])
    return user


def _upsert_item(
    *,
    media_id,
    media_type,
    title,
    genres,
    runtime,
    season_number=None,
    episode_number=None,
    authors=None,
    series_position=None,
    number_of_pages=None,
):
    """Create or refresh one sample item."""
    item, _created = Item.objects.update_or_create(
        media_id=media_id,
        source=Sources.MANUAL.value,
        media_type=media_type,
        season_number=season_number,
        episode_number=episode_number,
        defaults={
            "title": title,
            "genres": genres,
            "runtime_minutes": runtime,
            "synopsis": f"{title}. Sample row so this type has something to show.",
            "release_datetime": RELEASE,
            "authors": authors or [],
            "series_position": series_position,
            "number_of_pages": number_of_pages,
        },
    )
    return item


def _upsert_row(model, lookup, values):
    """Write ``values`` onto the row matching ``lookup``, without ``save()``.

    ``save()`` on a media row asks providers for metadata. Sample data must
    not do that.
    """
    concrete = {field.name for field in model._meta.concrete_fields}
    payload = {key: value for key, value in values.items() if key in concrete}
    row = model.objects.filter(**lookup).only("id").first()
    if row is None:
        model.objects.bulk_create([model(**lookup, **payload)])
        return
    model.objects.filter(pk=row.pk).update(**payload)


def _tracking(played, *, progress, status, score="8.0"):
    """Return the tracking columns a sample row should show."""
    return {
        "status": status,
        "score": Decimal(score),
        "scored_at": played,
        "progress": progress,
        "progressed_at": played,
        "start_date": played - timedelta(days=1),
        "end_date": played,
        "notes": "",
    }


def _seed_tracked(user, row, played):
    """Upsert one non-TV sample and its tracking row."""
    item = _upsert_item(
        media_id=row["media_id"],
        media_type=row["media_type"],
        title=row["title"],
        genres=row["genres"],
        runtime=row["runtime"],
        authors=row.get("authors"),
        series_position=row.get("series_position"),
        number_of_pages=row.get("number_of_pages"),
    )
    model = apps.get_model("app", row["model"])
    _upsert_row(
        model,
        {"user": user, "item": item},
        _tracking(played, progress=row["progress"], status=row.get("status", Status.IN_PROGRESS.value)),
    )


def _seed_show(user, show, played):
    """Upsert a show, one season, and two completed episodes."""
    show_item = _upsert_item(
        media_id=show["media_id"],
        media_type=MediaTypes.TV.value,
        title=show["title"],
        genres=["Mystery", "Drama"],
        runtime=52,
    )
    tv_model = apps.get_model("app", "TV")
    season_model = apps.get_model("app", "Season")
    episode_model = apps.get_model("app", "Episode")
    _upsert_row(
        tv_model,
        {"user": user, "item": show_item},
        _tracking(played, progress=0, status=Status.IN_PROGRESS.value),
    )
    tv = tv_model.objects.get(user=user, item=show_item)
    season_item = _upsert_item(
        media_id=show["media_id"],
        media_type=MediaTypes.SEASON.value,
        title=f"{show['title']} Season 1",
        genres=["Mystery", "Drama"],
        runtime=52,
        season_number=1,
    )
    _upsert_row(
        season_model,
        {"user": user, "item": season_item, "related_tv": tv},
        _tracking(played, progress=0, status=Status.IN_PROGRESS.value),
    )
    season = season_model.objects.get(user=user, item=season_item)
    for number in (1, 3):
        episode_item = _upsert_item(
            media_id=show["media_id"],
            media_type=MediaTypes.EPISODE.value,
            title=f"{show['title']} Episode {number}",
            genres=["Mystery", "Drama"],
            runtime=44,
            season_number=1,
            episode_number=number,
        )
        _upsert_row(
            episode_model,
            {"related_season": season, "item": episode_item},
            _tracking(
                played,
                progress=0,
                status=Status.COMPLETED.value,
                score="8.0",
            ),
        )


def _seed_music(user, played):
    """Upsert one artist, album, track, and play for this account."""
    artist_model = apps.get_model("app", "Artist")
    album_model = apps.get_model("app", "Album")
    track_model = apps.get_model("app", "Track")
    music_model = apps.get_model("app", "Music")
    tracker_model = apps.get_model("app", "AlbumTracker")
    artist, _created = artist_model.objects.get_or_create(
        musicbrainz_id=f"{SEED}-mina",
        defaults={"name": "Mina Cole", "genres": ["Jazz"]},
    )
    album, _created = album_model.objects.get_or_create(
        artist=artist,
        musicbrainz_release_group_id=f"{SEED}-room-tone",
        defaults={
            "title": "Room Tone",
            "release_date": RELEASE.date(),
            "genres": ["Jazz", "Electronic"],
        },
    )
    album_model.objects.filter(pk=album.pk).update(
        title="Room Tone",
        release_date=RELEASE.date(),
        genres=["Jazz", "Electronic"],
    )
    track, _created = track_model.objects.get_or_create(
        album=album,
        disc_number=1,
        track_number=1,
        defaults={
            "title": "Side A",
            "duration_ms": 246000,
            "genres": ["Jazz", "Electronic"],
        },
    )
    item = _upsert_item(
        media_id=f"{SEED}-music-{user.username}",
        media_type=MediaTypes.MUSIC.value,
        title="Side A",
        genres=["Jazz", "Electronic"],
        runtime=4,
    )
    _upsert_row(
        music_model,
        {"user": user, "item": item},
        {
            **_tracking(played, progress=3, status=Status.IN_PROGRESS.value, score="8.5"),
            "album": album,
            "artist": artist,
            "track": track,
        },
    )
    _upsert_row(
        tracker_model,
        {"user": user, "album": album},
        _tracking(played, progress=0, status=Status.IN_PROGRESS.value, score="8.0"),
    )


def _seed_cast():
    """Attach one cast credit to each sample movie."""
    person_model = apps.get_model("app", "Person")
    credit_model = apps.get_model("app", "ItemPersonCredit")
    person, _created = person_model.objects.get_or_create(
        source=Sources.MANUAL.value,
        source_person_id=f"{SEED}-ada",
        defaults={
            "name": "Ada Voss",
            "known_for_department": "Acting",
            "biography": "Ada Voss. Sample cast row so the person tile has a role.",
        },
    )
    movies = Item.objects.filter(
        source=Sources.MANUAL.value,
        media_type=MediaTypes.MOVIE.value,
        media_id__in=(f"{SEED}-movie-1", f"{SEED}-movie-2"),
    )
    for item in movies:
        credit_model.objects.get_or_create(
            item=item,
            person=person,
            role_type="cast",
            role="Night vendor",
            department="Acting",
        )
