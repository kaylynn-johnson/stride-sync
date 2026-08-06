from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from playlist.models import Playlist, Song, User


class BrowserTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,1024")
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def wait(self, timeout=10):
        return WebDriverWait(self.driver, timeout)

    def _login(self, username, password):
        # NOTE: layout.html's <head> has <meta name="username" ...>, which
        # shares the "username" name attribute with the login form's
        # <input name="username">. By.NAME matches whichever element has that
        # attribute first in document order (the meta tag), not the input, so
        # form fields must be scoped explicitly to `input[name=...]` here.
        self.driver.get(f"{self.live_server_url}{reverse('login')}")
        username_field = self.wait().until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name=username]"))
        )
        username_field.send_keys(username)
        self.driver.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "input[type=submit]").click()
        self.wait().until(EC.url_to_be(f"{self.live_server_url}{reverse('index')}"))


class SmokeTests(BrowserTestCase):

    def test_index_page_loads(self):
        self.driver.get(self.live_server_url)
        self.assertIn("StrideSync", self.driver.title)

    def test_static_assets_load_without_error(self):
        self.driver.get(self.live_server_url)
        logs = self.driver.get_log("browser")
        # favicon.ico is requested automatically by the browser; the app
        # doesn't define a route for it, and that 404 is expected/harmless.
        errors = [
            entry
            for entry in logs
            if entry["level"] == "SEVERE" and "favicon.ico" not in entry["message"]
        ]
        self.assertEqual(errors, [], f"Browser console errors: {errors}")


class RecommendationsPageTests(BrowserTestCase):

    def setUp(self):
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password=self.password
        )
        self.playlist = Playlist.objects.create(
            owner=self.user, name="Morning Run Mix", target_pace=8.0
        )
        self.matching_song = Song.objects.create(
            spotify_id="fe-matching", title="Matching Pace Song", album="Album A",
            pace=8.2, duration=200000, year=2020, genre="Rock", popularity=70,
        )
        self.mismatched_song = Song.objects.create(
            spotify_id="fe-mismatched", title="Mismatched Pace Song", album="Album B",
            pace=15.0, duration=200000, year=2020, genre="Jazz", popularity=50,
        )
        self.out_of_range_song = Song.objects.create(
            spotify_id="fe-outrange", title="Far Pace Song", album="Album C",
            pace=20.0, duration=200000, year=2015, genre="Blues", popularity=30,
        )
        self._login(self.user.username, self.password)

    def _open_recommendations(self):
        self.driver.get(
            f"{self.live_server_url}{reverse('recommendations', args=[self.user.username])}"
        )
        self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list-card")))

    def test_initial_load_renders_songs(self):
        self._open_recommendations()
        results_text = self.driver.find_element(By.ID, "recommendations-results").text
        self.assertIn(self.matching_song.title, results_text)
        self.assertIn(self.mismatched_song.title, results_text)
        self.assertIn(self.out_of_range_song.title, results_text)

    def test_filter_by_pace_updates_results(self):
        self._open_recommendations()

        self.driver.find_element(By.CSS_SELECTOR, "input[name=pace_min]").send_keys("7")
        self.driver.find_element(By.CSS_SELECTOR, "input[name=pace_max]").send_keys("9")
        self.driver.find_element(By.ID, "get-recommendations").click()

        self.wait().until(
            lambda d: self.mismatched_song.title
            not in d.find_element(By.ID, "recommendations-results").text
        )
        results_text = self.driver.find_element(By.ID, "recommendations-results").text
        self.assertIn(self.matching_song.title, results_text)
        self.assertNotIn(self.mismatched_song.title, results_text)
        self.assertNotIn(self.out_of_range_song.title, results_text)

    def test_more_info_modal_opens_and_closes(self):
        self._open_recommendations()

        self.driver.find_element(By.ID, f"more-info-{self.matching_song.id}").click()
        modal = self.wait().until(
            EC.visibility_of_element_located((By.ID, f"modal-content-{self.matching_song.id}"))
        )
        self.assertIn(self.matching_song.album, modal.text)

        self.driver.find_element(By.ID, f"close-{self.matching_song.id}").click()
        self.wait().until(
            EC.invisibility_of_element_located((By.ID, f"modal-content-{self.matching_song.id}"))
        )

    def test_add_song_within_pace_adds_directly(self):
        self._open_recommendations()

        self.driver.find_element(By.ID, f"add-{self.matching_song.id}").click()
        playlist_link = self.wait().until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, f"#playlists-{self.matching_song.id} li a")
            )
        )
        self.assertIn(self.playlist.name, playlist_link.text)
        playlist_link.click()

        alert = self.wait().until(EC.alert_is_present())
        self.assertIn("successfully added", alert.text)
        alert.accept()

        self.assertIn(self.matching_song, self.playlist.songs.all())

    def test_add_song_outside_pace_shows_warning_then_can_override(self):
        self._open_recommendations()

        self.driver.find_element(By.ID, f"add-{self.mismatched_song.id}").click()
        playlist_link = self.wait().until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, f"#playlists-{self.mismatched_song.id} li a")
            )
        )
        playlist_link.click()

        warning = self.wait().until(
            EC.visibility_of_element_located(
                (By.ID, f"warning-playlist-{self.mismatched_song.id}")
            )
        )
        self.assertIn("more than 1 minute outside", warning.text)
        warning.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        alert = self.wait().until(EC.alert_is_present())
        self.assertIn("successfully added", alert.text)
        alert.accept()

        self.assertIn(self.mismatched_song, self.playlist.songs.all())

    def test_add_song_outside_pace_can_be_cancelled(self):
        self._open_recommendations()

        self.driver.find_element(By.ID, f"add-{self.mismatched_song.id}").click()
        playlist_link = self.wait().until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, f"#playlists-{self.mismatched_song.id} li a")
            )
        )
        playlist_link.click()

        warning = self.wait().until(
            EC.visibility_of_element_located(
                (By.ID, f"warning-playlist-{self.mismatched_song.id}")
            )
        )
        warning.find_element(By.XPATH, ".//button[text()='No']").click()

        self.wait().until(
            EC.invisibility_of_element_located(
                (By.ID, f"warning-playlist-{self.mismatched_song.id}")
            )
        )
        self.assertNotIn(self.mismatched_song, self.playlist.songs.all())

    def test_pagination_click_loads_next_page(self):
        extra_songs = [
            Song.objects.create(
                spotify_id=f"fe-pagination-{i}", title=f"Pagination Song {i}",
                pace=8.0, duration=200000, year=2010, genre="Pop", popularity=i,
            )
            for i in range(1, 21)
        ]
        lowest_popularity_song = extra_songs[0]

        self._open_recommendations()
        self.assertEqual(
            self.driver.find_elements(By.ID, f"song-{lowest_popularity_song.id}"), []
        )

        pagination_links = self.driver.find_elements(By.CSS_SELECTOR, "#pagination a")
        pagination_links[-1].click()

        self.wait().until(
            EC.presence_of_element_located((By.ID, f"song-{lowest_popularity_song.id}"))
        )


class PublicPlaylistsPageTests(BrowserTestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="testpass123"
        )
        self.public_playlist = Playlist.objects.create(
            owner=self.owner, name="Public Mix", target_pace=8.0, is_public=True
        )
        self.private_playlist = Playlist.objects.create(
            owner=self.owner, name="Private Mix", target_pace=8.0, is_public=False
        )

    def test_renders_only_public_playlists(self):
        self.driver.get(f"{self.live_server_url}{reverse('playlists')}")
        self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list-card")))
        page_text = self.driver.find_element(By.ID, "all-playlists").text
        self.assertIn(self.public_playlist.name, page_text)
        self.assertNotIn(self.private_playlist.name, page_text)

    def test_view_playlist_navigates_to_indiv_playlist_page(self):
        self.driver.get(f"{self.live_server_url}{reverse('playlists')}")
        self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list-card")))

        self.driver.find_element(By.XPATH, "//button[text()='View Playlist']").click()
        self.wait().until(EC.url_contains(self.public_playlist.slug))
        self.assertIn(self.public_playlist.name, self.driver.find_element(By.TAG_NAME, "h1").text)


class ProfilePageTests(BrowserTestCase):

    def setUp(self):
        self.password = "testpass123"
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password=self.password
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password=self.password
        )
        self.public_playlist = Playlist.objects.create(
            owner=self.owner, name="Public Mix", target_pace=8.0, is_public=True
        )
        self.private_playlist = Playlist.objects.create(
            owner=self.owner, name="Private Mix", target_pace=8.0, is_public=False
        )

    def test_own_profile_shows_remove_button_and_all_playlists(self):
        self._login(self.owner.username, self.password)
        self.driver.get(f"{self.live_server_url}{reverse('profile', args=[self.owner.username])}")
        self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list-card")))

        page_text = self.driver.find_element(By.ID, "all-playlists").text
        self.assertIn(self.public_playlist.name, page_text)
        self.assertIn(self.private_playlist.name, page_text)
        self.assertEqual(len(self.driver.find_elements(By.CSS_SELECTOR, ".remove")), 2)

    def test_removing_playlist_updates_dom_and_deletes_it(self):
        self._login(self.owner.username, self.password)
        self.driver.get(f"{self.live_server_url}{reverse('profile', args=[self.owner.username])}")
        self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list-card")))

        self.driver.find_element(
            By.CSS_SELECTOR, f'.remove[data-playlist-id="{self.private_playlist.id}"]'
        ).click()

        alert = self.wait().until(EC.alert_is_present())
        alert.accept()

        self.wait().until(
            EC.invisibility_of_element_located((By.ID, f"playlist-{self.private_playlist.id}"))
        )
        self.assertFalse(Playlist.objects.filter(pk=self.private_playlist.pk).exists())

    def test_other_profile_hides_remove_button_and_private_playlists(self):
        self._login(self.other_user.username, self.password)
        self.driver.get(f"{self.live_server_url}{reverse('profile', args=[self.owner.username])}")
        self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list-card")))

        page_text = self.driver.find_element(By.ID, "all-playlists").text
        self.assertIn(self.public_playlist.name, page_text)
        self.assertNotIn(self.private_playlist.name, page_text)
        self.assertEqual(len(self.driver.find_elements(By.CSS_SELECTOR, ".remove")), 0)


class IndivPlaylistPageTests(BrowserTestCase):

    def setUp(self):
        self.password = "testpass123"
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password=self.password
        )
        self.playlist = Playlist.objects.create(
            owner=self.owner, name="Morning Run Mix", target_pace=8.0, is_public=False
        )
        self.song = Song.objects.create(
            spotify_id="fe-indiv-song", title="Steady Pace Song", album="Album D",
            pace=8.0, duration=200000, year=2020, genre="Rock", popularity=60,
        )
        self.playlist.songs.add(self.song)
        self._login(self.owner.username, self.password)
        self.driver.get(
            f"{self.live_server_url}{reverse('indiv_playlists', args=[self.playlist.slug])}"
        )

    def test_owner_can_toggle_public_private(self):
        make_public_btn = self.wait().until(EC.element_to_be_clickable((By.ID, "make-public")))
        make_public_btn.click()

        alert = self.wait().until(EC.alert_is_present())
        alert.accept()

        self.wait().until(EC.presence_of_element_located((By.ID, "make-private")))
        self.playlist.refresh_from_db()
        self.assertTrue(self.playlist.is_public)

    def test_song_more_info_modal_opens(self):
        self.driver.find_element(By.CSS_SELECTOR, ".more-info").click()
        modal = self.wait().until(
            EC.visibility_of_element_located((By.ID, f"modal-content-{self.song.id}"))
        )
        self.assertIn(self.song.album, modal.text)

    def test_owner_can_remove_song_from_playlist(self):
        self.driver.find_element(By.CSS_SELECTOR, ".remove").click()
        alert = self.wait().until(EC.alert_is_present())
        alert.accept()

        self.wait().until(
            EC.invisibility_of_element_located((By.ID, f"song-info-{self.song.id}"))
        )
        self.assertNotIn(self.song, self.playlist.songs.all())

    def test_copy_share_link_shows_url_in_alert(self):
        current_url = self.driver.current_url
        self.driver.find_element(By.CSS_SELECTOR, ".copy").click()

        alert = self.wait().until(EC.alert_is_present())
        self.assertIn(current_url, alert.text)
        alert.accept()
