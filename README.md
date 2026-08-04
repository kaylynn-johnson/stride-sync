# Stride Sync

Stride Sync is a full-stack Django web application that helps runners and walkers build music playlists matched to their pace. A user enters their target pace range (in minutes per mile), and Stride Sync converts that pace into a target cadence (steps per minute) and recommends songs from a database of over 500,000 tracks whose tempo (BPM) lines up with that cadence. Users can filter recommendations by pace range, release year, and genre, save songs into custom playlists, and make those playlists public so they can be shared with friends via a unique link.

## Distinctiveness and Complexity

Stride Sync is distinct from every other project in this course and from the two prior projects (the social network and the e-commerce/auction site) in both its domain and its core mechanic.

**Domain.** No other project in the course deals with fitness, music tempo, or pace-based recommendation. Rather than being a marketplace or a social feed, Stride Sync's central feature is a numerical matching engine: it converts a runner's pace into a physiologically meaningful cadence and matches that cadence against the tempo of real songs. This required domain research (translating mph/pace into steps-per-minute using average stride length) that isn't needed by any CRUD-style project, and it isn't a to-do list, blog, or e-commerce clone with a different coat of paint.

**Complexity.**

1. **Non-trivial backend math.** [playlist/utils.py](playlist/utils.py) implements the conversions between pace (min/mi), speed (mph), and cadence (BPM), using a piecewise formula that treats walking and running gaits differently (different average stride lengths above and below a 4 mph threshold, in both directions). This isn't boilerplate CRUD logic — it's the algorithmic core the entire app is built around, and every song recommendation depends on it being correct in both directions (BPM → pace when songs are imported, and pace → BPM implicitly through the `pace` field itself).

2. **Large, real dataset with a custom ETL pipeline.** The app ships two custom Django management commands, [load_artists.py](playlist/management/commands/load_artists.py) and [load_songs.py](playlist/management/commands/load_songs.py), that stream a ~550,000-row Spotify dataset (`playlist/management/data/songs.csv`) and a ~70,000-row artist dataset from CSV into PostgreSQL. The song loader converts each track's raw tempo into a running pace at import time, validates every row with Django's `full_clean()`, skips malformed rows without aborting the whole batch, and then performs a second pass to resolve the comma-separated artist ID/name lists into a many-to-many `Song`–`Artist` relationship using bulk inserts through the `through` model — all batched (5,000/1,000 rows at a time) so it can run against real-world data volume without exhausting memory. This is considerably more involved than seeding a database with a fixtures file.

3. **A filterable, paginated JSON API consumed by hand-written JavaScript.** [playlist/filters.py](playlist/filters.py) defines a `django_filters.FilterSet` that exposes range filters on pace and year and a choice filter on genre. The `/api/songs/` endpoint in [playlist/views.py](playlist/views.py) applies that filter set, slices the result to the top 100 matches, and paginates them 20 at a time with Django's `Paginator`. On the front end, [playlist/static/playlist/recommendations.js](playlist/static/playlist/recommendations.js) fetches this endpoint asynchronously, renders results and pagination controls without a page reload, and keeps the URL's query string in sync with `history.pushState` so filtered/paginated views are bookmarkable and shareable — the same single-page-app pattern used throughout the project (see also [playlists.js](playlist/static/playlist/playlists.js), [profile.js](playlist/static/playlist/profile.js), and [indivPlaylist.js](playlist/static/playlist/indivPlaylist.js)), rather than relying on full server-rendered page reloads for every interaction.

4. **A real relational data model with several non-obvious constraints.** [playlist/models.py](playlist/models.py) defines a custom `User` model (email required and unique), a many-to-many `Song`–`Artist` relationship, database indexes on the fields actually used for filtering/sorting (pace, year, popularity, genre), and a `Playlist` model whose `slug` field is generated with a cryptographically random URL-safe token (`secrets.token_urlsafe`) rather than a sequential ID or a user-editable string, so that a playlist's shareable link can't be trivially guessed or enumerated. Playlist visibility (`is_public`) is enforced server-side in `indiv_playlists` — a private playlist returns a 404 to anyone but its owner — rather than merely being hidden in the UI.

5. **A full authentication and authorization system built by hand**, not scaffolded by a third-party package: registration, login, logout, and a change-password flow all live in [playlist/views.py](playlist/views.py), and access control is enforced at the view layer with `@login_required` and explicit ownership/visibility checks (e.g. `profile_api` returns only public playlists when a visitor looks at someone else's profile, but all playlists when a user looks at their own).

6. **A containerized, environment-configured deployment.** The project runs against PostgreSQL (not SQLite) via `docker-compose.yml`, which wires together a Django web container and a Postgres container with a health check gating startup order, and reads all secrets and database configuration from environment variables ([stride_sync/settings.py](stride_sync/settings.py)) rather than hardcoding them — a deliberately more production-like setup than the course's default single-process, SQLite-backed projects.

Taken together, the pace/tempo conversion math, the large real-world dataset with a two-stage bulk-import pipeline, the filterable paginated JSON API driving a dynamic front end, and the token-based shareable-playlist model push this well beyond the complexity of a simple CRUD app, while the running/music-pace-matching concept is unlike anything else built in this course.

## What's contained in each file

**Project-level**
- `manage.py` — Django's command-line utility for running the dev server, migrations, and management commands.
- `stride_sync/settings.py` — Project configuration: installed apps, middleware, the PostgreSQL connection (read from environment variables), the custom `AUTH_USER_MODEL`, and static files config.
- `stride_sync/urls.py` — Root URL configuration; includes the admin site and the `playlist` app's URLs.
- `stride_sync/asgi.py` / `stride_sync/wsgi.py` — Standard Django ASGI/WSGI entry points.
- `requirements.txt` — Python dependencies (Django, `psycopg` for PostgreSQL, `django-filter`, etc.).
- `Dockerfile` — Builds the Django app image.
- `docker-compose.yml` — Orchestrates the `web` (Django) and `db` (PostgreSQL) containers, including a Postgres health check.
- `.env` — Environment variables consumed by both `settings.py` and `docker-compose.yml` (not committed; see Setup below).

**The `playlist` app**
- `playlist/models.py` — Defines `User` (custom user model with a required/unique email), `Artist`, `Song` (with pace, duration, year, genre, popularity, and indexes on the fields used for filtering), and `Playlist` (owned by a user, with a randomly generated shareable `slug` and an `is_public` flag).
- `playlist/views.py` — All page and API views: authentication (`login_view`, `logout_view`, `register`, `change_password`), profile pages, the recommendations page, the playlist list and detail pages, and the JSON API endpoints (`songs_api`, `playlists_api`, `modify_songs_api`, `profile_api`).
- `playlist/urls.py` — Maps URLs to the views above, including the `/api/...` routes used by the front-end JavaScript.
- `playlist/filters.py` — `SongFilter`, a `django_filters.FilterSet` exposing pace-range, year-range, and genre filters used by both the recommendations form and the `/api/songs/` endpoint.
- `playlist/utils.py` — Pure conversion functions between pace (min/mi), speed (mph), and cadence (BPM); the mathematical core of the pace-matching feature.
- `playlist/admin.py` — Registers all four models with the Django admin site, with a custom site header/title.
- `playlist/tests.py` — Placeholder for Django's test framework (`TestCase` import scaffolded by `startapp`).
- `playlist/templatetags/math_filters.py` — A custom template filter (`timeString`) that converts a song's duration in milliseconds to an `MM:SS` string for display.
- `playlist/templatetags/pagination_tags.py` — Template tags (`url_replace`, `url_delete`) for building pagination/query-string links that preserve existing GET parameters.
- `playlist/management/commands/load_artists.py` — Management command that bulk-loads `Artist` rows from a CSV file.
- `playlist/management/commands/load_songs.py` — Management command that bulk-loads `Song` rows from a CSV file (converting tempo to pace on import) and links each song to its artists.
- `playlist/management/data/` — Source CSVs for the two load commands (`artists.csv`, `songs.csv`, plus small `short_*` samples for quick local testing); excluded from version control via `.gitignore` due to size.
- `playlist/migrations/` — Django's auto-generated database migration history for the `playlist` app.

**Templates** (`playlist/templates/playlist/`)
- `layout.html` — Base template: navbar (which changes based on authentication state), CSRF meta tag, and shared `<head>`/`<body>` structure that every other template extends.
- `index.html` — Landing page describing the four-step Stride Sync flow.
- `login.html` / `register.html` / `change_password.html` — Authentication forms.
- `profile.html` — A user's profile page, listing their (or, for other users, their public) playlists via the profile API.
- `recommendations.html` — The pace/year/genre filter form and the container the JavaScript populates with recommended songs.
- `playlists.html` — Browse all public playlists across all users.
- `indiv_playlist.html` — A single playlist's detail page: its songs, and (for the owner) controls to make it public/private, copy its share link, or remove songs.

**Static assets** (`playlist/static/playlist/`)
- `recommendations.js` — Fetches filtered/paginated songs from `/api/songs/`, renders them, handles the "more info" and "add to playlist" modals, and creates new playlists inline.
- `playlists.js` — Loads and renders the public playlist browsing page.
- `profile.js` — Loads and renders a profile's playlists, including a remove action when viewing your own profile.
- `indivPlaylist.js` — Handles making a playlist public/private, copying its share link, and removing songs from it.
- `styles.css` — Custom styling layered on top of Bootstrap.

## How to run the application

Stride Sync is configured to run via Docker Compose with a PostgreSQL database.

1. **Set up environment variables.** Create a `.env` file in the project root with:
   ```
   DJANGO_SECRET_KEY=<any-random-string>
   POSTGRES_DB=stride_sync
   POSTGRES_USER=stride_sync
   POSTGRES_PASSWORD=<a-password>
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```
2. **Build and start the containers:**
   ```
   docker compose up --build
   ```
   This starts a PostgreSQL container and the Django app, waiting for the database to report healthy before the app starts.
3. **Run migrations** (in a second terminal, once the containers are up):
   ```
   docker compose exec web python manage.py migrate
   ```
4. **Load the song/artist data.** Full CSVs (`playlist/management/data/artists.csv` and `songs.csv`) are large (~550,000 songs / ~70,000 artists); smaller `short_artists.csv` / `short_songs.csv` samples are included for a quicker local setup:
   ```
   docker compose exec web python manage.py load_artists playlist/management/data/short_artists.csv
   docker compose exec web python manage.py load_songs playlist/management/data/short_songs.csv
   ```
5. **Create an admin account (optional):**
   ```
   docker compose exec web python manage.py createsuperuser
   ```
6. **Visit the app** at `http://localhost:8000`. Register a new account, then use "Recommendations" to enter a target pace and browse matching songs, or "Playlists" to browse playlists other users have made public.

Alternatively, the app can be run outside Docker with `pip install -r requirements.txt` and a locally running PostgreSQL instance whose connection details match the environment variables above, followed by the same `migrate` / `load_artists` / `load_songs` / `runserver` steps via `python manage.py ...` directly.

## Additional information

- **Data source.** The song dataset is a Spotify tracks dataset (tempo, duration, year, genre, popularity, and artist metadata per track). The pace shown for each song is computed once, at import time, by `load_songs.py` converting the song's raw tempo (BPM) into a running pace via the walking/running cadence model in `utils.py` — it is not recalculated per request.
- **Pace-mismatch warning.** When adding a song to an existing playlist, `recommendations.js` compares the song's pace to the playlist's target pace and — if they differ by more than one minute per mile — shows a confirmation prompt before allowing the add, rather than silently accepting mismatched songs.
- **No third-party account/API integration.** Despite the Spotify-derived dataset, Stride Sync does not call the Spotify API at runtime; all song data is imported once into the app's own PostgreSQL database, so the app has no external runtime dependency for its core recommendation feature.
- **Browser support.** The front end relies on `fetch`, template literals, and `history.pushState`, so a reasonably modern evergreen browser is assumed.
- **Known scope limits.** `playlist/tests.py` is currently a scaffold with no test cases written, and there is no automated CI configured for this repository.
