# Source - https://stackoverflow.com/a/22735278
# Posted by Ben Wilber
# Retrieved 2026-07-27, License - CC BY-SA 3.0

from django import template
register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    d = request.GET.copy()
    d[field] = value
    return d.urlencode()

@register.simple_tag
def url_delete(request, field):
    d = request.GET.copy()
    del d[field]
    return d.urlencode()
