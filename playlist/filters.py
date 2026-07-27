import django_filters

from .models import Song

# As of July 27, 2026, the genres in the dataset are: ['Rock', 'Hip-Hop', 'Classical', 'Electronic', 'Pop', 'Folk', 'R&B', 'Jazz', 'Blues', 'Country']

GENRES = [
    ('Rock', 'Rock'),
    ('Hip-Hop', 'Hip-Hop'),
    ('Classical', 'Classical'),
    ('Electronic', 'Electronic'),
    ('Pop', 'Pop'),
    ('Folk', 'Folk'),
    ('R&B', 'R&B'),
    ('Jazz', 'Jazz'),
    ('Blues', 'Blues'),
    ('Country', 'Country'),
]

# In Django shell, run set(Song.objects.values_list('genre', flat=True).distinct()) to get the distinct genres in the database. Then, update the GENRES list above accordingly.

class SongFilter(django_filters.FilterSet):
    tempo_min = django_filters.NumberFilter(field_name='tempo', lookup_expr='gte')
    tempo_max = django_filters.NumberFilter(field_name='tempo', lookup_expr='lte')
    year = django_filters.AllValuesFilter(field_name='year')
    #year_min = django_filters.NumberFilter(field_name='year', lookup_expr='gte')
    #year_max = django_filters.NumberFilter(field_name='year', lookup_expr='lte')
    genre = django_filters.MultipleChoiceFilter(field_name='genre', lookup_expr='icontains', choices=GENRES)

    class Meta:
        model = Song
        fields = ['tempo_min', 'tempo_max', 'year', 'genre']