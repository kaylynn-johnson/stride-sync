import csv
from django.core.management.base import BaseCommand
from playlist.models import Artist, Song
from django.core.exceptions import ValidationError

from playlist.utils import speed_to_pace, bpm_to_speed

class Command(BaseCommand):
    help = 'Import data from a CSV file into the Song model'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        batch_size = 5000
        all_songs = []
        artist_list = []

        Song.objects.all().delete()  # Clear existing songs before loading new ones

        with open(csv_file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                try:
                    pace = round(speed_to_pace(bpm_to_speed(float(row.get('tempo')))), 1)
                    song = Song(
                        spotify_id=row['id'],
                        title=row['name'],
                        album=row['album_name'],
                        pace=pace,
                        duration=row['duration_ms'],
                        year=row['year'],
                        genre=row['genre'],
                        popularity=row['popularity']
                    )
                    song.full_clean()
                    all_songs.append(song)
                    artist_ids = row['artist_ids']
                    artist_names = row['artists']
                    artist_list.append((artist_ids, artist_names))
                except ValidationError as e:
                    self.stderr.write(f"Validation error in row: {row}. Error: {e}")
                except Exception as e:
                    self.stderr.write(f"Error in row: {row}. Error: {e}")
            print(f"Total songs to create: {len(all_songs)}")
            Song.objects.bulk_create(all_songs, batch_size=batch_size, ignore_conflicts=True)

        Through = Song.artists.through

        artist_links = []
        for song, (artist_ids, artist_names) in zip(all_songs, artist_list):
            try:
                song_instance = Song.objects.get(spotify_id=song.spotify_id)
                for (artist_id, artist_name) in zip(artist_ids.split(','), artist_names.split(',')):
                    artist_id = artist_id.replace('"', '').replace("[", "").replace("]", "").strip()  # Clean up the artist_id
                    artist_name = artist_name.replace('"', '').replace("[", "").replace("]", "").strip() # Clean up the artist_name
                    artist_instance, _ = Artist.objects.get_or_create(spotify_id=artist_id, defaults={'name': artist_name})
                    artist_links.append(Through(song_id=song_instance.id, artist_id=artist_instance.id))
            except Artist.DoesNotExist:
                self.stderr.write(f"Artist with spotify_id {artist_id} does not exist.")
            except Song.DoesNotExist:
                self.stderr.write(f"Song with spotify_id {song.spotify_id} does not exist.")

        Through.objects.bulk_create(artist_links, batch_size=batch_size, ignore_conflicts=True)
