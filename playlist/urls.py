
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("change_password", views.change_password, name="change_password"),
    path("profile/<str:target_username>", views.profile, name="profile"),
    path("profile/<str:username>/recommendations", views.recommendations, name="recommendations"),
    path("playlists", views.playlists, name="playlists"),
    path("playlists/<str:slug>", views.indiv_playlists, name="indiv_playlists"),

    # API Routes
    path("api/songs/", views.songs_api, name="songs_api"),
    path("api/playlists/", views.playlists_api, name="playlists_api"),
    path("api/playlists/songs/", views.modify_songs_api, name="modify_songs_api"),
    path("api/profile/", views.profile_api, name="profile_api")
]
