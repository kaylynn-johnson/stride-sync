# Stride Sync

Stride Sync is a full-stack Django web application that helps runners and walkers build music playlists that match their pace. A user enters their target pace range (in minutes per mile), and Stride Sync recommends songs from a database of over 500,000 tracks whose tempo (BPM) lines up with that cadence. Users can filter recommendations by pace range, release year, and genre, save songs into custom playlists, and make those playlists public so they can be shared with friends via a unique link.

## Distinctiveness and Complexity

Stride Sync is distinct from the other projects in this course in both its purpose and scope/complexity.

**Purpose.** No other project in the course deals with fitness, music tempo, or pace-based recommendation. Rather than being a marketplace or a social feed, Stride Sync's central feature is a numerical matching engine: it converts each song's tempo in a running/walking pace that can be used for recommendations for users. This required additional research (translating mph/pace into steps-per-minute using average stride length) that isn't needed by any CRUD-style project.

**Complexity.**

1. **Non-trivial backend math.** [playlist/utils.py](playlist/utils.py) implements the conversions between pace (min/mi), speed (mph), and cadence (BPM), using a piecewise formula that treats walking and running gaits differently (different average stride lengths above and below a 4 mph threshold, in both directions). This conversion is the core of the app as it is the basis for all the recommendations. The piecewise formula was found on [StepsCal](https://www.stepscal.com/mph-to-steps-calculator) which assumes an average adult whose height is 5' 7". The formula is applied at song ingest to convert tempo (BPM) to pace (min/mi) for the database.

2. **Large, real dataset with a custom ETL pipeline.** The app includes two custom Django management commands, [load_artists.py](playlist/management/commands/load_artists.py) and [load_songs.py](playlist/management/commands/load_songs.py), that stream a ~550,000-row Spotify dataset (`playlist/management/data/songs.csv`) and a ~70,000-row artist dataset from CSV into PostgreSQL. The song loader converts each track's raw tempo into a running pace at import time, validates every row with Django's `full_clean()`, skips malformed rows without aborting the whole batch, and then performs a second pass to resolve the comma-separated artist ID/name lists into a many-to-many `Song`–`Artist` relationship using bulk inserts through the `through` model. This is considerably more involved than seeding a database with a fixed file. The dataset was extracted from Serkan Tüysüz's 550K Spotify Songs: Audio, Lyrics & Genres [Kaggle](https://www.kaggle.com/datasets/serkantysz/550k-spotify-songs-audio-lyrics-and-genres) database, transformed by the management commands, and loaded into the PostgreSQL database.

3. **A filterable, paginated JSON API** [playlist/filters.py](playlist/filters.py) defines a `django_filters.FilterSet` that exposes range filters on pace and year and a choice filter on genre. The `/api/songs/` endpoint in [playlist/views.py](playlist/views.py) applies that filter set, slices the result to the top 100 matches, and paginates them 20 at a time with Django's `Paginator`. On the front end, [playlist/static/playlist/recommendations.js](playlist/static/playlist/recommendations.js) fetches this endpoint asynchronously, renders results and pagination controls without a page reload, and keeps the URL's query string in sync with `history.pushState` so previous queries can be returned to. The same single-page-app pattern is used throughout the project (see also [playlists.js](playlist/static/playlist/playlists.js), [profile.js](playlist/static/playlist/profile.js), and [indivPlaylist.js](playlist/static/playlist/indivPlaylist.js)), rather than relying on full server-rendered page reloads for every interaction. Since there are many updating pieces with changing recommendation inputs, requesting for more song information, adding songs to playlists, and creating new playlists on the fly, using APIs controlled from front-end JavaScript is the obvious choice for a smooth user experience. 

4. **A real relational data model with several non-obvious constraints.** [playlist/models.py](playlist/models.py) defines a basic `User` model and custom `Artist`, `Song` and `Playlist` models. The `Song` model features a many-to-many `Song`–`Artist` relationship to handle the many artists a song can have and the many songs an artist can author. Database indexes for the `Song` model on the fields actually used for filtering/sorting (pace, year, popularity, genre) greatly decreases query times across a 550,000+ song dataset to where it seems instanteous to users. The `Playlist` model features a `slug` field that is generated with a cryptographically random URL-safe token (`secrets.token_urlsafe`) rather than a sequential ID or a user-editable string, so that a playlist's shareable link can't be trivially guessed or enumerated. Playlist visibility (`is_public`) is enforced server-side in `indiv_playlists` preventing unauthorized users from viewing private playlists.

5. **A containerized, environment-configured deployment.** The project uses Docker and PostgreSQL to prove a production-like setup. Due to the large nature of the dataset, PostgreSQL was chosen over Django's native SQLite. A Dockerfile instructs on the creation of the Django web image, and the `docker-compose.yml` file instructs on the configuration of the web and PostgreSQL containers. Health checks on the startup of the PostgreSQL container must pass before the Django web container will start. Secrets and database configurations are read from environmental variables to further mimic a production-like setup.

In all, the pace/tempo conversion math, the large real-world dataset with a two-stage bulk-import pipeline, the filterable paginated JSON API driving a dynamic front end for recommendations, and the token-based shareable-playlist model push this well beyond the complexity of a simple CRUD app, while the running/music-pace-matching concept is unlike anything else built in this course.

## What's contained in each file

**Project-level**
- `manage.py` — Django's command-line utility for running the dev server, migrations, and management commands.
- `stride_sync/settings.py` — Project configuration: installed apps, middleware, the PostgreSQL connection (read from environment variables), the custom `AUTH_USER_MODEL`, and static files config.
- `stride_sync/urls.py` — Root URL configuration; includes the admin site and the `playlist` app's URLs.
- `requirements.txt` — Python dependencies (Django, `psycopg` for PostgreSQL, `django-filter`, etc.).
- `Dockerfile` — Builds the Django app image.
- `docker-compose.yml` — Orchestrates the `web` (Django) and `db` (PostgreSQL) containers, including a Postgres health check.
- `.env` — Environment variables consumed by both `settings.py` and `docker-compose.yml` (not committed; see Setup below).

**The `playlist` app**
- `playlist/models.py` — Defines `User`, `Artist`, `Song` (with pace, duration, year, genre, popularity, and indexes on the fields used for filtering), and `Playlist` (owned by a user, with a randomly generated shareable `slug` and an `is_public` flag).
- `playlist/views.py` — All page and API views: authentication (`login_view`, `logout_view`, `register`, `change_password`), profile pages, the recommendations page, the playlist list and detail pages, and the JSON API endpoints (`songs_api`, `playlists_api`, `modify_songs_api`, `profile_api`).
- `playlist/urls.py` — Maps URLs to the views above, including the `/api/...` routes used by the front-end JavaScript.
- `playlist/filters.py` — `SongFilter`, a `django_filters.FilterSet` exposing pace-range, year-range, and genre filters used by both the recommendations form and the `/api/songs/` endpoint.
- `playlist/utils.py` — Pure conversion functions between pace (min/mi), speed (mph), and cadence (BPM)
- `playlist/admin.py` — Registers all four models with the Django admin site, with a custom site header/title.
- `playlist/templatetags/math_filters.py` — A custom template filter (`timeString`) that converts a song's duration in milliseconds to an `MM:SS` string for display.
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
- `indiv_playlist.html` — A single playlist's detail page: its songs, shareable link, and (for the owner) controls to make it public/private or remove songs.

**Static assets** (`playlist/static/playlist/`)
- `recommendations.js` — Fetches filtered/paginated songs from `/api/songs/`, renders them, handles the "more info" and "add to playlist" modals, and creates new playlists inline.
- `playlists.js` — Loads and renders the public playlist browsing page for all public playlists.
- `profile.js` — Loads and renders a profile's playlists, including a remove action when viewing your own profile.
- `indivPlaylist.js` — Handles making a playlist public/private, copying its share link, and removing songs from it.
- `styles.css` — Custom styling layered on top of Bootstrap.

## How to run the application

Stride Sync is configured to run via Docker Compose with a PostgreSQL database.

1. **Set up environment variables.** Create a `.env` file in the project root with:
   ```
   DJANGO_SECRET_KEY=<any-random-string>
   POSTGRES_DB=stride_sync
   POSTGRES_USER=stride_sync_user
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
4. **Load the song/artist data.** Full CSVs (`playlist/management/data/artists.csv` and `songs.csv`) are large (~550,000 songs / ~70,000 artists); smaller `artists_small.csv` / `songs_small.csv` samples are included for a quicker local setup:
   ```
   docker compose exec web python manage.py load_artists playlist/management/data/artists_small.csv
   docker compose exec web python manage.py load_songs playlist/management/data/songs_small.csv
   ```
   If the full CSV is desired, download straight from [Kaggle](https://www.kaggle.com/datasets/serkantysz/550k-spotify-songs-audio-lyrics-and-genres).
5. **Create an admin account (optional):**
   ```
   docker compose exec web python manage.py createsuperuser
   ```
6. **Visit the app** at `http://localhost:8000`. Register a new account, then use "Recommendations" to enter a target pace and browse matching songs, or "Playlists" to browse playlists other users have made public.

Alternatively, the app can be run outside Docker with `pip install -r requirements.txt` and a locally running PostgreSQL instance whose connection details match the environment variables above, followed by the same `migrate` / `load_artists` / `load_songs` / `runserver` steps via `python manage.py ...` directly.

## Additional information

- **Data source.** The song dataset is a Spotify tracks dataset (tempo, duration, year, genre, popularity, and artist metadata per track). The pace shown for each song is computed once, at import time, by `load_songs.py` converting the song's raw tempo (BPM) into a running pace via the walking/running cadence model in `utils.py`. It is not recalculated per request.
- **Pace-mismatch warning.** When adding a song to an existing playlist, `recommendations.js` compares the song's pace to the playlist's target pace. If they differ by more than one minute per mile, a confirmation prompt is shown to confirm the user wants to add the song.
- **No third-party account/API integration.** Despite the Spotify-derived dataset, Stride Sync does not call the Spotify API at runtime; all song data is imported once into the app's own PostgreSQL database, so the app has no external runtime dependency for its core recommendation feature.
- **Browser support.** The front end relies on `fetch`, template literals, and `history.pushState`, so a reasonably modern browser is assumed.