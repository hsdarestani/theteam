from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation

from .html_translation import translate_html_content
from .identity_models import TeamIdentity


class BrandingLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        identity = None
        previous_language = translation.get_language()
        try:
            identity = TeamIdentity.load()
            request.team_identity = identity
            try:
                translation.activate(identity.resolved_language)
            except OSError:
                translation.activate("de")
        except (OperationalError, ProgrammingError):
            pass

        try:
            response = self.get_response(request)
            if identity is not None:
                response["Content-Language"] = identity.resolved_language
                content_type = response.get("Content-Type", "")
                if (
                    "text/html" in content_type
                    and not getattr(response, "streaming", False)
                    and not request.path.startswith("/admin/")
                ):
                    charset = response.charset or "utf-8"
                    content = response.content.decode(charset)
                    content = translate_html_content(
                        content,
                        identity.resolved_language,
                        identity.custom_translations,
                    )
                    response.content = content.encode(charset)
                    response["Content-Length"] = str(len(response.content))
            return response
        finally:
            translation.activate(previous_language)


class InitialSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed = {reverse("setup"), reverse("health"), reverse("team_logo")}
        if request.path.startswith("/static/") or request.path.startswith("/media/") or request.path.startswith("/admin/"):
            return self.get_response(request)
        if request.path not in allowed and not get_user_model().objects.exists():
            return redirect("setup")
        return self.get_response(request)
