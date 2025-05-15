from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # při registraci nového User vytvoř i Profile
        Profile.objects.create(user=instance)
    else:
        # při úpravě User uložíme i případné změny profile
        instance.profile.save()
