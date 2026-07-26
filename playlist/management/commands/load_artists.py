import csv
from django.core.management.base import BaseCommand
from playlist.models import Artist
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Import data from a CSV file into the Artist model'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        batch_size = 1000
        all_artists = []

        with open(csv_file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                try:
                    artist = Artist(
                        spotify_id=row['id'],
                        name=row['name']
                    )
                    artist.full_clean()
                    all_artists.append(artist)
                except ValidationError as e:
                    self.stderr.write(f"Validation error in row: {row}. Error: {e}")
                except Exception as e:
                    self.stderr.write(f"Error in row: {row}. Error: {e}")

        Artist.objects.bulk_create(all_artists, batch_size=batch_size, ignore_conflicts=True)
