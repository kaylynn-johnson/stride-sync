import json

from django.contrib.auth import get_user
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from playlist.models import Artist, Playlist, Song, User


class RegisterViewTests(TransactionTestCase):
    # TransactionTestCase (not TestCase): the register view catches
    # IntegrityError internally rather than letting it propagate. Under
    # TestCase's wrapping per-test atomic transaction, Postgres marks that
    # transaction aborted regardless of the in-app catch, so any further
    # query in the same test raises TransactionManagementError. Production
    # requests run in autocommit mode (no such wrapping transaction), so this
    # is purely a test-isolation-strategy mismatch, not an application bug.

    def test_get_renders_register_form(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "playlist/register.html")

    def test_post_creates_user_and_logs_in(self):
        response = self.client.post(reverse("register"), {
            "username": "newrunner",
            "email": "newrunner@example.com",
            "password": "testpass123",
            "confirmation": "testpass123",
        })
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(User.objects.filter(username="newrunner").exists())
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_post_rejects_mismatched_passwords(self):
        response = self.client.post(reverse("register"), {
            "username": "newrunner",
            "email": "newrunner@example.com",
            "password": "testpass123",
            "confirmation": "different",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords must match.")
        self.assertFalse(User.objects.filter(username="newrunner").exists())

    def test_post_rejects_duplicate_username(self):
        User.objects.create_user(
            username="existing", email="existing@example.com", password="testpass123"
        )
        response = self.client.post(reverse("register"), {
            "username": "existing",
            "email": "different@example.com",
            "password": "testpass123",
            "confirmation": "testpass123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")
        self.assertEqual(User.objects.filter(username="existing").count(), 1)


class LoginViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.password = "testpass123"
        cls.user = User.objects.create_user(
            username="alice", email="alice@example.com", password=cls.password
        )

    def test_get_renders_login_form(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "playlist/login.html")

    def test_post_valid_credentials_logs_in_and_redirects(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.username,
            "password": self.password,
        })
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_post_invalid_credentials_shows_message(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.username,
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username and/or password.")
        self.assertFalse(get_user(self.client).is_authenticated)


class LogoutViewTests(TestCase):

    def test_logout_clears_session_and_redirects(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="testpass123"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("index"))
        self.assertFalse(get_user(self.client).is_authenticated)


class ChangePasswordViewTests(TestCase):

    def setUp(self):
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password=self.password
        )

    def test_requires_login(self):
        response = self.client.get(reverse("change_password"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('change_password')}"
        )

    def test_get_renders_form_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("change_password"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "playlist/change_password.html")

    def test_post_changes_password_with_correct_current_password(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("change_password"), {
            "current_password": self.password,
            "new_password": "newpass456",
            "confirmation": "newpass456",
        })
        self.assertRedirects(response, reverse("index"))
        self.client.logout()
        self.assertTrue(self.client.login(username=self.user.username, password="newpass456"))

    def test_post_rejects_mismatched_new_passwords(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("change_password"), {
            "current_password": self.password,
            "new_password": "newpass456",
            "confirmation": "different",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New passwords must match.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_post_rejects_incorrect_current_password(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("change_password"), {
            "current_password": "wrongcurrent",
            "new_password": "newpass456",
            "confirmation": "newpass456",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current password is incorrect.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))


class SongsApiTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="testpass123"
        )

        cls.slow_rock = Song.objects.create(
            spotify_id="filter-slow-rock", title="Slow Rock", pace=11.0,
            duration=200000, year=1985, genre="Rock", popularity=40,
        )
        cls.fast_electronic = Song.objects.create(
            spotify_id="filter-fast-electronic", title="Fast Electronic", pace=6.5,
            duration=180000, year=2018, genre="Electronic", popularity=80,
        )
        cls.mid_pop = Song.objects.create(
            spotify_id="filter-mid-pop", title="Mid Pop", pace=8.5,
            duration=190000, year=2005, genre="Pop", popularity=60,
        )
        cls.artist = Artist.objects.create(spotify_id="filter-artist-1", name="Test Artist")
        cls.mid_pop.artists.add(cls.artist)

        # Enough same-pace songs to push results past one page (20/page).
        for i in range(25):
            Song.objects.create(
                spotify_id=f"pagination-song-{i}",
                title=f"Pagination Song {i}",
                pace=7.0,
                duration=200000,
                year=2010,
                genre="Rock",
                popularity=i,
            )

    def _get(self, params):
        self.client.force_login(self.user)
        return self.client.get(reverse("songs_api"), params)

    def test_requires_login(self):
        response = self.client.get(reverse("songs_api"), {"pace_min": "0", "pace_max": "20"})
        self.assertEqual(response.status_code, 302)

    def test_filters_by_pace_range(self):
        response = self._get({"pace_min": "6", "pace_max": "7"})
        data = json.loads(response.content)
        titles = [song["title"] for song in data["recommended_songs"]]
        self.assertIn("Fast Electronic", titles)
        self.assertNotIn("Slow Rock", titles)

    def test_missing_pace_param_returns_unfiltered_results(self):
        # Documents current django_filters behavior: an invalid (missing required
        # pace) filter form falls back to the full unfiltered queryset.
        response = self._get({})
        data = json.loads(response.content)
        self.assertGreater(data["num_pages"], 1)

    def test_filters_by_genre(self):
        response = self._get({"pace_min": "0", "pace_max": "20", "genre": "Electronic"})
        data = json.loads(response.content)
        titles = [song["title"] for song in data["recommended_songs"]]
        self.assertIn("Fast Electronic", titles)
        self.assertNotIn("Slow Rock", titles)

    def test_filters_by_year_range(self):
        response = self._get({
            "pace_min": "0", "pace_max": "20", "year_min": "2015", "year_max": "2020",
        })
        data = json.loads(response.content)
        titles = [song["title"] for song in data["recommended_songs"]]
        self.assertIn("Fast Electronic", titles)
        self.assertNotIn("Slow Rock", titles)

    def test_pagination(self):
        response = self._get({"pace_min": "6", "pace_max": "8", "page": "2"})
        data = json.loads(response.content)
        self.assertEqual(data["page"], 2)

        response = self._get({"pace_min": "6", "pace_max": "8", "page": "not-a-number"})
        data = json.loads(response.content)
        self.assertEqual(data["page"], 1)

        response = self._get({"pace_min": "6", "pace_max": "8", "page": "999"})
        data = json.loads(response.content)
        self.assertEqual(data["page"], data["num_pages"])

    def test_response_includes_artist_names_keyed_by_song_id(self):
        response = self._get({"pace_min": "0", "pace_max": "20", "genre": "Pop"})
        data = json.loads(response.content)
        self.assertEqual(data["artists"][str(self.mid_pop.id)], self.artist.name)


class ModifySongsApiTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="testpass123"
        )
        cls.playlist = Playlist.objects.create(
            owner=cls.user, name="Morning Run Mix", target_pace=8.0
        )
        cls.matching_song = Song.objects.create(
            spotify_id="modify-matching", title="Matching Pace", pace=8.2,
            duration=200000, year=2020,
        )
        cls.mismatched_song = Song.objects.create(
            spotify_id="modify-mismatched", title="Mismatched Pace", pace=15.0,
            duration=200000, year=2020,
        )

    def _post(self, payload, login=True):
        if login:
            self.client.force_login(self.user)
        return self.client.post(
            reverse("modify_songs_api"), data=json.dumps(payload), content_type="application/json"
        )

    def test_requires_login(self):
        response = self._post(
            {"playlist_name": self.playlist.name, "song_id": self.matching_song.id, "add": True},
            login=False,
        )
        self.assertEqual(response.status_code, 302)

    def test_requires_post_method(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("modify_songs_api"))
        self.assertEqual(response.status_code, 400)

    def test_add_song_to_playlist(self):
        response = self._post(
            {"playlist_name": self.playlist.name, "song_id": self.matching_song.id, "add": True}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.matching_song, self.playlist.songs.all())

    def test_remove_song_from_playlist(self):
        self.playlist.songs.add(self.matching_song)
        response = self._post(
            {"playlist_name": self.playlist.name, "song_id": self.matching_song.id, "add": False}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.matching_song, self.playlist.songs.all())

    def test_add_ignores_pace_mismatch(self):
        # Documents current behavior: the tempo-mismatch warning/override is
        # entirely client-side (recommendations.js); the endpoint itself never
        # checks pace, so a wildly mismatched song is still added successfully.
        response = self._post(
            {"playlist_name": self.playlist.name, "song_id": self.mismatched_song.id, "add": True}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.mismatched_song, self.playlist.songs.all())

    def test_nonexistent_playlist_or_song_raises_not_found(self):
        # Documents current behavior: neither lookup is wrapped in a try/except
        # in the view, so a missing playlist/song propagates as an unhandled
        # DoesNotExist rather than a clean 404 response.
        with self.assertRaises(Playlist.DoesNotExist):
            self._post(
                {"playlist_name": "Does Not Exist", "song_id": self.matching_song.id, "add": True}
            )

        with self.assertRaises(Song.DoesNotExist):
            self._post({"playlist_name": self.playlist.name, "song_id": 999999, "add": True})


class PlaylistsApiTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="testpass123"
        )
        cls.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="testpass123"
        )
        cls.song = Song.objects.create(
            spotify_id="playlists-api-song", title="Steady Pace", pace=8.0,
            duration=200000, year=2020,
        )
        cls.public_playlist = Playlist.objects.create(
            owner=cls.owner, name="Public Mix", target_pace=8.0, is_public=True
        )
        cls.private_playlist = Playlist.objects.create(
            owner=cls.owner, name="Private Mix", target_pace=8.0, is_public=False
        )

    def _put(self, payload, user=None):
        if user is not None:
            self.client.force_login(user)
        return self.client.put(
            reverse("playlists_api"), data=json.dumps(payload), content_type="application/json"
        )

    def test_get_lists_only_public_playlists(self):
        response = self.client.get(reverse("playlists_api"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn(self.public_playlist.id, data["ids"])
        self.assertNotIn(self.private_playlist.id, data["ids"])

    def test_post_requires_login(self):
        response = self.client.post(
            reverse("playlists_api"),
            data=json.dumps({"name": "New Mix", "pace": 8.0, "song_id": self.song.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Playlist.objects.filter(name="New Mix").exists())

    def test_post_creates_playlist_for_authenticated_user(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("playlists_api"),
            data=json.dumps({"name": "New Mix", "pace": 8.0, "song_id": self.song.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        playlist = Playlist.objects.get(name="New Mix")
        self.assertEqual(playlist.owner, self.owner)
        self.assertIn(self.song, playlist.songs.all())

    def test_put_requires_login(self):
        response = self._put({"playlist_id": self.public_playlist.id, "public": False})
        self.assertEqual(response.status_code, 401)
        self.public_playlist.refresh_from_db()
        self.assertTrue(self.public_playlist.is_public)

    def test_put_requires_ownership(self):
        response = self._put(
            {"playlist_id": self.public_playlist.id, "public": False}, user=self.other_user
        )
        self.assertEqual(response.status_code, 403)
        self.public_playlist.refresh_from_db()
        self.assertTrue(self.public_playlist.is_public)

    def test_put_toggles_public_status_for_owner(self):
        response = self._put(
            {"playlist_id": self.private_playlist.id, "public": True}, user=self.owner
        )
        self.assertEqual(response.status_code, 200)
        self.private_playlist.refresh_from_db()
        self.assertTrue(self.private_playlist.is_public)

    def test_put_removes_playlist_for_owner(self):
        response = self._put(
            {"playlist_id": self.private_playlist.id, "remove": True}, user=self.owner
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Playlist.objects.filter(pk=self.private_playlist.pk).exists())

    def test_unsupported_method_returns_400(self):
        self.client.force_login(self.owner)
        response = self.client.delete(reverse("playlists_api"))
        self.assertEqual(response.status_code, 400)


class IndivPlaylistViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="testpass123"
        )
        cls.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="testpass123"
        )
        cls.public_playlist = Playlist.objects.create(
            owner=cls.owner, name="Public Mix", target_pace=8.0, is_public=True
        )
        cls.private_playlist = Playlist.objects.create(
            owner=cls.owner, name="Private Mix", target_pace=8.0, is_public=False
        )

    def test_public_playlist_visible_to_anonymous_user(self):
        response = self.client.get(
            reverse("indiv_playlists", args=[self.public_playlist.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_public_playlist_visible_to_other_authenticated_user(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse("indiv_playlists", args=[self.public_playlist.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_private_playlist_visible_to_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("indiv_playlists", args=[self.private_playlist.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_private_playlist_returns_404_for_non_owner(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse("indiv_playlists", args=[self.private_playlist.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_private_playlist_returns_404_for_anonymous_user(self):
        response = self.client.get(
            reverse("indiv_playlists", args=[self.private_playlist.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse("indiv_playlists", args=["doesnotexist"]))
        self.assertEqual(response.status_code, 404)


class ProfileApiTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="testpass123"
        )
        cls.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="testpass123"
        )
        cls.public_playlist = Playlist.objects.create(
            owner=cls.owner, name="Public Mix", target_pace=8.0, is_public=True
        )
        cls.private_playlist = Playlist.objects.create(
            owner=cls.owner, name="Private Mix", target_pace=8.0, is_public=False
        )

    def test_requires_login(self):
        response = self.client.get(reverse("profile_api"), {"username": self.owner.username})
        self.assertEqual(response.status_code, 302)

    def test_own_profile_includes_private_and_public_playlists(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("profile_api"), {"username": self.owner.username})
        data = json.loads(response.content)
        self.assertIn(self.public_playlist.id, data["ids"])
        self.assertIn(self.private_playlist.id, data["ids"])

    def test_other_users_profile_includes_only_public_playlists(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("profile_api"), {"username": self.owner.username})
        data = json.loads(response.content)
        self.assertIn(self.public_playlist.id, data["ids"])
        self.assertNotIn(self.private_playlist.id, data["ids"])

    def test_unknown_username_raises_not_found(self):
        # Documents current behavior: User.DoesNotExist isn't caught in the view.
        self.client.force_login(self.owner)
        with self.assertRaises(User.DoesNotExist):
            self.client.get(reverse("profile_api"), {"username": "ghostuser"})
