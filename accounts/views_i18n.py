"""
Internationalization views for language switching.
"""

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation
from django.views.decorators.http import require_POST


@require_POST
def set_language(request):
    """
    Set the user's language preference and redirect back to the previous page.

    Expects a POST parameter 'language' with a valid language code.
    """
    next_url = request.POST.get("next", request.headers.get("referer", "/"))
    language = request.POST.get("language")

    if language and language in dict(settings.LANGUAGES):
        translation.activate(language)
        response = HttpResponseRedirect(next_url)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
        return response

    return HttpResponseRedirect(next_url)
