from django.utils import timezone
from .models import TeamEvent

def navigation_context(request):
    next_event = None
    if request.user.is_authenticated:
        next_event = TeamEvent.objects.filter(starts_at__gte=timezone.now()).first()
    return {"nav_next_event": next_event}
