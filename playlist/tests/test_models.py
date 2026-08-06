from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from playlist.models import Artist, Playlist, Song, User


class UserModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="testpass123"
        )

    def test_str_returns_username(self):
        self.assertEqual(str(self.user), self.user.username)

    def test_email_is_required(self):
        user = User(username="no_email_user", email="")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_email_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="alice2", email=self.user.email, password="testpass123"
                )


class ArtistModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(spotify_id="artist-001", name="Aurora Beats")

    def test_str_returns_name(self):
        self.assertEqual(str(self.artist), self.artist.name)

    def test_name_is_required(self):
        artist = Artist(spotify_id="artist-002", name="")
        with self.assertRaises(ValidationError):
            artist.full_clean()

    def test_spotify_id_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Artist.objects.create(spotify_id=self.artist.spotify_id, name="Someone Else")


class SongModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.artist1 = Artist.objects.create(spotify_id="song-artist-1", name="Aurora Beats")
        cls.artist2 = Artist.objects.create(spotify_id="song-artist-2", name="Nova Sound")

        cls.song_high_pop = Song.objects.create(
            spotify_id="song-high-pop",
            title="Runner High",
            album="Momentum",
            pace=8.5,
            duration=210000,
            year=2016,
            genre="Electronic",
            popularity=90,
        )
        cls.song_high_pop.artists.add(cls.artist1, cls.artist2)

        cls.song_mid_pop = Song.objects.create(
            spotify_id="song-mid-pop",
            title="Solo Track",
            pace=9.0,
            duration=180000,
            year=1998,
            genre="Rock",
            popularity=50,
        )

        cls.song_low_pop = Song.objects.create(
            spotify_id="song-low-pop",
            title="Slow Burn",
            pace=11.0,
            duration=240000,
            year=1975,
            genre="Jazz",
            popularity=10,
        )
        cls.song_low_pop.artists.add(cls.artist1)

        cls.song_no_popularity = Song.objects.create(
            spotify_id="song-no-popularity",
            title="Unranked",
            pace=7.0,
            duration=195000,
            year=2005,
        )

    def test_str_includes_all_artist_names(self):
        song_str = str(self.song_high_pop)
        self.assertTrue(song_str.startswith(f"{self.song_high_pop.title} by "))
        self.assertIn(self.artist1.name, song_str)
        self.assertIn(self.artist2.name, song_str)

    def test_str_uses_unknown_artist_when_no_artists(self):
        self.assertEqual(
            str(self.song_mid_pop), f"{self.song_mid_pop.title} by Unknown Artist"
        )

    def test_spotify_id_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Song.objects.create(
                    spotify_id=self.song_high_pop.spotify_id,
                    title="Duplicate",
                    pace=8.0,
                    duration=200000,
                    year=2020,
                )

    def test_required_fields_enforced(self):
        base_kwargs = dict(
            spotify_id="required-fields-song",
            title="Complete Song",
            pace=7.5,
            duration=200000,
            year=2021,
        )
        for field in ["title", "pace", "duration", "year"]:
            with self.subTest(field=field):
                kwargs = dict(base_kwargs)
                kwargs[field] = "" if field == "title" else None
                song = Song(**kwargs)
                with self.assertRaises(ValidationError):
                    song.full_clean()

    def test_album_and_genre_are_optional(self):
        song = Song(
            spotify_id="optional-album-genre",
            title="No Metadata",
            album=None,
            genre=None,
            pace=8.0,
            duration=200000,
            year=2020,
        )
        song.full_clean()

    def test_popularity_is_optional(self):
        self.song_no_popularity.full_clean()

    def test_popularity_cannot_exceed_100(self):
        song = Song(
            spotify_id="popularity-too-high",
            title="Too Popular",
            pace=8.0,
            duration=200000,
            year=2020,
            popularity=101,
        )
        with self.assertRaises(ValidationError):
            song.full_clean()

    def test_popularity_cannot_be_negative(self):
        song = Song(
            spotify_id="popularity-negative",
            title="Negatively Popular",
            pace=8.0,
            duration=200000,
            year=2020,
            popularity=-1,
        )
        with self.assertRaises(ValidationError):
            song.full_clean()

    def test_default_ordering_is_by_popularity_desc(self):
        songs = Song.objects.filter(
            pk__in=[self.song_high_pop.pk, self.song_mid_pop.pk, self.song_low_pop.pk]
        )
        self.assertEqual(
            list(songs), [self.song_high_pop, self.song_mid_pop, self.song_low_pop]
        )


class PlaylistModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="playlist_owner", email="owner@example.com", password="testpass123"
        )
        cls.song = Song.objects.create(
            spotify_id="playlist-song-1",
            title="Steady Pace",
            pace=8.0,
            duration=200000,
            year=2020,
        )
        cls.playlist = Playlist.objects.create(
            owner=cls.owner, name="Morning Run Mix", target_pace=8.0
        )

    def test_str_returns_name_and_owner_username(self):
        self.assertEqual(
            str(self.playlist), f"{self.playlist.name} by {self.owner.username}"
        )

    def test_slug_is_auto_generated_when_not_provided(self):
        self.assertTrue(self.playlist.slug)
        self.assertLessEqual(len(self.playlist.slug), 11)

    def test_explicit_slug_is_preserved(self):
        playlist = Playlist.objects.create(
            owner=self.owner, name="Custom Slug Mix", target_pace=8.0, slug="customslug1"
        )
        self.assertEqual(playlist.slug, "customslug1")

    def test_slug_is_not_regenerated_on_update(self):
        original_slug = self.playlist.slug
        self.playlist.name = "Morning Run Mix (Updated)"
        self.playlist.save()
        self.assertEqual(self.playlist.slug, original_slug)

    def test_slug_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Playlist.objects.create(
                    owner=self.owner,
                    name="Slug Collision",
                    target_pace=8.0,
                    slug=self.playlist.slug,
                )

    def test_is_public_defaults_to_false(self):
        self.assertFalse(self.playlist.is_public)

    def test_owner_is_required(self):
        playlist = Playlist(name="No Owner", target_pace=8.0, slug="validslug1")
        with self.assertRaises(ValidationError):
            playlist.full_clean()

    def test_target_pace_is_required(self):
        playlist = Playlist(owner=self.owner, name="No Pace", slug="validslug2")
        with self.assertRaises(ValidationError):
            playlist.full_clean()

    def test_deleting_owner_cascades_to_playlist(self):
        temp_owner = User.objects.create_user(
            username="temp_owner", email="temp_owner@example.com", password="testpass123"
        )
        temp_playlist = Playlist.objects.create(
            owner=temp_owner, name="Temporary", target_pace=8.0
        )
        temp_owner.delete()
        self.assertFalse(Playlist.objects.filter(pk=temp_playlist.pk).exists())

    def test_songs_can_be_added_and_are_optional(self):
        playlist = Playlist.objects.create(
            owner=self.owner, name="Empty Playlist", target_pace=8.0
        )
        self.assertEqual(playlist.songs.count(), 0)

        playlist.songs.add(self.song)
        self.assertIn(self.song, playlist.songs.all())
        self.assertIn(playlist, self.song.songs.all())
