from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models
import secrets

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)

    def __str__(self):
        return f"{self.username}"

class Artist(models.Model):
    spotify_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"
    
class Song(models.Model):
    spotify_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    album = models.CharField(max_length=255, blank=True, null=True)
    artists = models.ManyToManyField(Artist, related_name='songs')
    pace = models.FloatField(blank=False, null=False)
    duration = models.IntegerField(blank=False, null=False)
    year = models.IntegerField(blank=False, null=False)
    genre = models.CharField(max_length=255, blank=True, null=True)
    popularity = models.PositiveIntegerField(validators=[MaxValueValidator(100)], blank=True, null=True)

    class Meta:
       indexes = [
            models.Index(fields=['pace'], name='pace_idx'),
            models.Index(fields=['year'], name='year_idx'),
            models.Index(fields=['popularity'], name='popularity_idx'),
            models.Index(fields=['genre'], name='genre_idx'),
        ]
       ordering = ['-popularity']

    def __str__(self):
        return f"{self.title} by {', '.join([artist.name for artist in self.artists.all()]) if self.artists.exists() else 'Unknown Artist'}"

class Playlist(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=255)
    target_pace = models.FloatField(blank=False, null=False)
    slug = models.CharField(max_length=11, unique=True) # token is encoded, so max_length is set to 11 to ensure the token is not truncated
    is_public = models.BooleanField(default=False)
    songs = models.ManyToManyField(Song, related_name='songs', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = secrets.token_urlsafe(8)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} by {self.owner.username}"