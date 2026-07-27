
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("change_password", views.change_password, name="change_password"),
    path("profile/<str:username>", views.profile, name="profile"),
    path("profile/<str:username>/recommendations", views.recommendations, name="recommendations"),
    path("playlists", views.playlists, name="playlists"),
    path("playlists/<str:slug>", views.indiv_playlists, name="indiv_playlists")
    #path("following/<str:username>", views.FollowingListView.as_view(), name="following")
]
