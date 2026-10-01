# accounts/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Safely create or save the Profile instance whenever a User is created or updated."""
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        # Ensures that if an existing user somehow lacks a profile, it gets created safely
        Profile.objects.get_or_create(user=instance)
        instance.profile.save()