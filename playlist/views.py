from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from .models import User, Artist, Song, Playlist
from .filters import SongFilter
from .utils import pace_to_speed, speed_to_pace, speed_to_bpm, bpm_to_speed

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

@login_required
def change_password(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
                return HttpResponseRedirect(reverse("login"))
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirmation = request.POST["confirmation"]

        # Check if new password matches confirmation
        if new_password != confirmation:
            return render(request, "playlist/change_password.html", {
                "message": "New passwords must match."
            })

        # Check if current password is correct
        user = request.user
        if not user.check_password(current_password):
            return render(request, "playlist/change_password.html", {
                "message": "Current password is incorrect."
            })

        # Change the password
        user.set_password(new_password)
        user.save()
        login(request, user)  # Log the user in with the new password
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "playlist/change_password.html")

@login_required
def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    return render(request, "playlist/profile.html", {
        "user": user
    })

@login_required
def recommendations(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    # Initial load of all songs
    song_filter = SongFilter(request.GET, queryset=Song.objects.all())
    song_form = song_filter.form.as_div()

    return render(request, "playlist/recommendations.html", {
        "user": user,
        "song_form": song_form
    })

@login_required
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

@login_required
def songs_api(request):
    filters = request.GET
    filter_dict = filters.dict()

    song_filter = SongFilter(data=filter_dict)
    recommended_songs = song_filter.qs[:100]

    page = request.GET["page"] if "page" in request.GET else 1

    paginator = Paginator(recommended_songs, 20)
    try:
        songs = paginator.page(page)
    except PageNotAnInteger:
        songs = paginator.page(1)
    except EmptyPage:
        songs = paginator.page(paginator.num_pages)

    data = {
            "recommended_songs": list(songs.object_list.values()),
            "artists": {song.id: ', '.join([artist.name for artist in song.artists.all()]) for song in songs.object_list},
            "page": songs.number,
            "num_pages": paginator.num_pages,
        }
    return JsonResponse(data, safe=False)

@login_required
def playlists_api(request):

    playlists = Playlist.objects.filter(owner=User.objects.get(username=request.user.username))

    data = {
            "titles": [p.title for p in playlists],
            "target_paces": [p.target_pace for p in playlists]
    }

    return JsonResponse(data, safe=False)
