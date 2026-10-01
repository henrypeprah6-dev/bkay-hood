# accounts/context_processors.py
from .models import Notification, Message

def unread_counts(request):
    """Context processor to make unread notification and message counts available globally in templates."""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
        unread_messages = Message.objects.filter(receiver=request.user, is_read=False).count()
        
        return {
            'unread_notifications_count': unread_notifications,
            'unread_messages_count': unread_messages,
        }
    return {
        'unread_notifications_count': 0,
        'unread_messages_count': 0,
    }