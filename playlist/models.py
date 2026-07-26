from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models

class User(AbstractUser):
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
    tempo = models.FloatField(blank=False, null=False)
    duration = models.IntegerField(blank=False, null=False)
    year = models.IntegerField(blank=False, null=False)
    genre = models.CharField(max_length=255, blank=True, null=True)
    popularity = models.PositiveIntegerField(validators=[MaxValueValidator(100)], blank=True, null=True)

    class Meta:
       indexes = [
            models.Index(fields=['tempo'], name='tempo_idx'),
            models.Index(fields=['year'], name='year_idx'),
            models.Index(fields=['popularity'], name='popularity_idx'),
            models.Index(fields=['genre'], name='genre_idx'),
    ]

    def __str__(self):
        return f"{self.title} by {self.artists.all().first().name if self.artists.exists() else 'Unknown Artist'}"

