from django.contrib import admin
from .models import User, Artist, Song, Playlist

# Register your models here.
admin.site.site_header = "Stride Sync Admin"
admin.site.site_title = "Stride Sync Admin Portal"
admin.site.index_title = "Welcome to the Stride Sync Admin Portal"
admin.site.register(User)
admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Playlist)