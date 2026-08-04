from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import json

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
def profile(request, target_username):
    try:
        target_user = User.objects.get(username=target_username)
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

    return render(request, "playlist/profile.html", {
        "target_user": target_user
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


def playlists(request):

    return render(request, "playlist/playlists.html")

def indiv_playlists(request, slug):
    try:
        playlist = Playlist.objects.get(slug=slug)
        if (playlist.owner != request.user) and not playlist.is_public:
            # throw error the non-owner is trying to view a private playlist
            return HttpResponse("Playlist is private", status=404)
        songs = playlist.songs.all()
        many_to_many_info = zip(
            songs,
            [', '.join([artist.name for artist in song.artists.all()]) for song in songs]
        )
    except Playlist.DoesNotExist:
        return HttpResponse("Playlist not found.", status=404)

    return render(request, "playlist/indiv_playlist.html", {
        "playlist": playlist,
        "songs": many_to_many_info
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


def playlists_api(request):

    if request.method == "GET":
        # view playlists
        playlists = Playlist.objects.filter(is_public=True)

        data = {
                "ids": [p.id for p in playlists],
                "titles": [p.name for p in playlists],
                "target_paces": [p.target_pace for p in playlists],
                "slugs": [p.slug for p in playlists],
                "owners": [p.owner.username for p in playlists],
                "num_songs": [p.songs.all().count() for p in playlists]
        }

        return JsonResponse(data, safe=False)

    if request.method == "POST":
        # creates a playlist
        data = json.loads(request.body)
        name = data.get("name")
        target_pace = data.get("pace")
        song = Song.objects.get(id=data.get("song_id"))
        owner = request.user
        playlist = Playlist(
            owner=owner,
            name=name,
            target_pace=target_pace,
        )
        playlist.save()

        playlist.songs.add(song)
        #playlist.save()
        return JsonResponse({"message": "Successfully created playlist"})

    if request.method == "PUT":
        # changes the viewability of the playlist
        data = json.loads(request.body)
        id = data.get("playlist_id")
        playlist = Playlist.objects.get(id=id)
        if data.get("public") is not None:
            public = data.get("public")
            playlist.is_public = public
            playlist.save()
            return JsonResponse({"message": "Successfully changed status"})
        if data.get("remove") is not None:
            playlist.delete()
            return JsonResponse({"message": "Successfully removed playlist"})
        return JsonResponse({"message": "No action taken"})


    return JsonResponse({"error": "Must use POST, GET or PUT at this route"}, status=400)

@login_required
def modify_songs_api(request):
    # add song to existing playlist
    if request.method == "POST":
        data = json.loads(request.body)
        playlist = Playlist.objects.get(owner=request.user, name=data.get('playlist_name'))
        song = Song.objects.get(id=data.get('song_id'))
        if data.get('add'):
            playlist.songs.add(song)
            return JsonResponse({"message": "Successfully added song to playlist"})
        else:
            playlist.songs.remove(song)
            return JsonResponse({"message": "Successfully removed song to playlist"})

    return JsonResponse({"error": "Muse use POST at this route"}, status=400)

@login_required
def profile_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "Must use GET method at this route"}, status=400)

    target_username = request.GET["username"]

    if target_username == request.user.username:
        # Viewing own profile
        playlists = Playlist.objects.filter(owner=request.user)
    else:
        # Viewing someone else's profile
        playlists = Playlist.objects.filter(owner=User.objects.get(username=target_username), is_public=True)

    data = {
        "ids": [p.id for p in playlists],
        "titles": [p.name for p in playlists],
        "target_paces": [p.target_pace for p in playlists],
        "slugs": [p.slug for p in playlists],
        "owners": [p.owner.username for p in playlists],
        "num_songs": [p.songs.all().count() for p in playlists]
    }

    return JsonResponse(data, safe=False)