from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth. mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

from .models import User, Artist, Song, Playlist

# Create your views here.

def index(request):
    return render(request, "playlist/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "playlist/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "playlist/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "playlist/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError as e:
            return render(request, "playlist/register.html", {
                "message": f"Username {username} is already taken. Error: {str(e)}"
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "playlist/register.html")


def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    return render(request, "playlist/profile.html", {
        "user": user
    })

def recommendations(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    # Placeholder for recommendations logic
    recommended_songs = []  # This should be replaced with actual recommendation logic

    return render(request, "playlist/recommendations.html", {
        "user": user,
        "recommended_songs": recommended_songs
    })

def playlists(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    user_playlists = Playlist.objects.filter(owner=user)

    return render(request, "playlist/playlists.html", {
        "playlists": user_playlists
    })

def indiv_playlists(request, slug):
    try:
        playlist = Playlist.objects.get(slug=slug)
    except Playlist.DoesNotExist:
        return HttpResponse("Playlist not found.", status=404)

    return render(request, "playlist/playlist.html", {
        "playlist": playlist
    })