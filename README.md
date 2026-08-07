# StrideSync

**Live app:** [stride-sync.up.railway.app](https://stride-sync.up.railway.app/)

Music playlists that match your running or walking pace.

Enter a target pace (minutes per mile) and StrideSync recommends songs whose tempo lines up with your cadence, drawn from a database of 550,000+ tracks. Save songs into playlists, keep them private, or share them publicly via a unique link.

## Features

- **Pace-based recommendations** — filter by pace range, release year, and genre; each song's tempo is pre-converted to a running/walking pace at import time.
- **Playlists** — create, browse, and manage playlists; make any playlist public to share via a non-guessable link, or keep it private.
- **Pace-mismatch warning** — adding a song more than a minute off a playlist's target pace prompts for confirmation first.
- **Accounts** — registration, login, and password changes, all server-validated.

## Tech stack

Django 6 · PostgreSQL · vanilla JS (fetch-driven, no framework) · Bootstrap 4 + custom CSS · Docker

## Getting started

Requires Docker and Docker Compose.

1. **Environment variables.** Create a `.env` file in the project root:
   ```
   DJANGO_SECRET_KEY=<any-random-string>
   POSTGRES_DB=stride_sync
   POSTGRES_USER=stride_sync_user
   POSTGRES_PASSWORD=<a-password>
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```
2. **Build and start:**
   ```
   docker compose up --build
   ```
3. **Migrate** (second terminal, once containers are up):
   ```
   docker compose exec web python manage.py migrate
   ```
4. **Load song/artist data.** Small sample CSVs are included for a quick local setup:
   ```
   docker compose exec web python manage.py load_artists playlist/management/data/artists_small.csv
   docker compose exec web python manage.py load_songs playlist/management/data/songs_small.csv
   ```
   For the full dataset (~550K songs / ~70K artists), download the CSVs from [Kaggle](https://www.kaggle.com/datasets/serkantysz/550k-spotify-songs-audio-lyrics-and-genres) into `playlist/management/data/` and point the commands at `artists.csv` / `songs.csv` instead.
5. **Create an admin account** (optional):
   ```
   docker compose exec web python manage.py createsuperuser
   ```
6. **Visit** `http://localhost:8000`.

Without Docker: `pip install -r requirements.txt`, point the same environment variables at a local PostgreSQL instance, then run the same `migrate` / `load_artists` / `load_songs` / `runserver` steps directly.

## Tests

```
docker compose exec web python manage.py test
```

Covers models, views/API, and (with `pip install selenium` and a local Chrome/Chromium + driver) a headless-browser suite in `playlist/tests/test_frontend.py`. CI (`.github/workflows/ci.yml`) runs lint, checks, and the full suite on every push and PR to `main`.

## Production

The `Dockerfile` runs `collectstatic` at build time and starts `gunicorn` (not the dev server); `docker-compose.yml` overrides this back to `runserver` for local dev only. A few things are environment-driven and matter for a real deploy:

- `DJANGO_DEBUG=False` (default) enables HTTPS redirect, secure cookies, HSTS, and a strict Content-Security-Policy; it also turns *on* rate limiting on login/register/password-change (5/min per IP), which stays off otherwise so local dev and the test suite aren't rate-limited against themselves.
- `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated) add your real domain.
- `REDIS_URL`, if set, backs the rate-limit cache so limits are enforced consistently across multiple gunicorn workers; without it, falls back to a per-process cache.
- `WEB_CONCURRENCY` sets the gunicorn worker count (default 3).

## Project layout

```
manage.py
stride_sync/            Django project config (settings, urls, wsgi)
playlist/
├─ models.py             User, Artist, Song, Playlist
├─ views.py               page + JSON API views
├─ filters.py              pace/year/genre FilterSet
├─ utils.py                 tempo ↔ pace ↔ speed conversions
├─ management/commands/      load_artists, load_songs (CSV → DB)
├─ management/data/           source CSVs (large ones gitignored)
├─ templates/playlist/         one template per page + shared layout.html
├─ static/playlist/             per-page JS + styles.css
└─ tests/                        models, views/API, and Selenium frontend tests
```

## Data source

Song and artist data comes from Serkan Tüysüz's [550K Spotify Songs: Audio, Lyrics & Genres](https://www.kaggle.com/datasets/serkantysz/550k-spotify-songs-audio-lyrics-and-genres) dataset on Kaggle. It's imported once via the management commands above — StrideSync never calls the Spotify API at runtime.
