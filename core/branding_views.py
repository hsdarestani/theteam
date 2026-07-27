import mimetypes

from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET

from .identity_models import TeamIdentity


@require_GET
def team_logo(request):
    """Backward-compatible logo endpoint.

    New templates use the persistent ``/media/`` URL served by Caddy. Keeping
    this route avoids breaking cached pages while ensuring a missing or stale
    file never becomes an application-level 500 error.
    """

    identity = TeamIdentity.load()
    if not identity.logo:
        raise Http404("No team logo has been uploaded.")

    try:
        file_handle = identity.logo.open("rb")
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise Http404("The uploaded team logo is unavailable.") from exc

    content_type = mimetypes.guess_type(identity.logo.name)[0] or "application/octet-stream"
    response = FileResponse(file_handle, content_type=content_type)
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response
