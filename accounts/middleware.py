# accounts/middleware.py
from django.utils import timezone
from .models import Profile

class UpdateLastSeenMiddleware:
    """Updates the user's last_seen timestamp on requests if authenticated."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            Profile.objects.filter(user=request.user).update(last_seen=timezone.now())
        response = self.get_response(request)
        return response