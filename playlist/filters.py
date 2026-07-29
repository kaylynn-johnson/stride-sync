import django_filters
from django import forms

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
    pace = django_filters.RangeFilter(field_name='pace', label='Pace Range (min/mi)', required=True)
    year = django_filters.RangeFilter(field_name='year', label='Year Range')
    genre = django_filters.ChoiceFilter(field_name='genre', lookup_expr='icontains', choices=GENRES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Song
        fields = ['pace', 'year', 'genre']