from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

class InitialSetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed = {reverse("setup"), reverse("health")}
        if request.path.startswith("/static/") or request.path.startswith("/admin/"):
            return self.get_response(request)
        if request.path not in allowed and not get_user_model().objects.exists():
            return redirect("setup")
        return self.get_response(request)
