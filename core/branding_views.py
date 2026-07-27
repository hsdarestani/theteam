import mimetypes

from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET

from .identity_models import TeamIdentity


@require_GET
def team_logo(request):
    identity = TeamIdentity.load()
    if not identity.logo:
        raise Http404("No team logo has been uploaded.")

    content_type = mimetypes.guess_type(identity.logo.name)[0] or "application/octet-stream"
    response = FileResponse(identity.logo.open("rb"), content_type=content_type)
    response["Cache-Control"] = "private, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response
