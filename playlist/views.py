from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

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

    # Placeholder for recommendations logic
    # Determine which filters were applied by the user
    # Filter must contain pace and could contain genre & year
    # Will sort by popularity and return the top 30 songs that match the filters
    filters = request.GET
    filter_dict = filters.dict()
    message = filter_dict
    #if not filter_dict.get("pace"):
    #    return render(request, "playlist/recommendations.html", {
    #        "user": user,
    #        "message": "Pace is required for recommendations."
    #    })

    # convert pace to tempo range for filtering
    # considering 30 seconds before and after the pace for a range of songs
    #filter_dict["tempo_min"] = speed_to_bpm(pace_to_speed(float(filter_dict.get("pace")) - 0.5)) 
    #filter_dict["tempo_max"] = speed_to_bpm(pace_to_speed(float(filter_dict.get("pace")) + 0.5))

    # Remove pace from filter_dict as it's not a field in the Song model
    #del filter_dict["pace"]

    song_filter = SongFilter(data=filter_dict)
    recommended_songs = song_filter.qs[:30]
    song_form = song_filter.form.as_div()
    #print('hi', flush=True)
    #print(song_form)  # Debugging line to check the form structure

    return render(request, "playlist/recommendations.html", {
        "user": user,
        "recommended_songs": recommended_songs,
        "song_form": song_form,
        "message": message
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