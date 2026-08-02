from django import template
import math as m
register = template.Library()

@register.filter
def timeString(ms):
    try:
        given_seconds = ms / 1000
        minutes = m.floor((given_seconds) / 60)
        seconds = m.floor(given_seconds - (minutes * 60))
        timeString =  f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"
        return timeString
    except (ValueError, TypeError):
        return ''