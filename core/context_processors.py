from django.db import OperationalError, ProgrammingError
from django.utils import timezone

from .branding import get_ui
from .identity_models import TeamIdentity
from .models import TeamEvent


def navigation_context(request):
    next_event = None
    if request.user.is_authenticated:
        next_event = TeamEvent.objects.filter(starts_at__gte=timezone.now()).first()
    return {"nav_next_event": next_event}


def team_identity_context(request):
    identity = getattr(request, "team_identity", None)
    if identity is None:
        try:
            identity = TeamIdentity.load()
        except (OperationalError, ProgrammingError):
            identity = TeamIdentity()

    return {
        "team_identity": identity,
        "ui": get_ui(
            identity.resolved_language,
            identity.custom_translations,
        ),
    }
