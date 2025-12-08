from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, ServiceProvider

@receiver(post_save, sender=User)
def create_provider_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'provider':
        ServiceProvider.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_provider_profile(sender, instance, **kwargs):
    if instance.user_type == 'provider':
        try:
            instance.provider_profile.save()
        except ServiceProvider.DoesNotExist:
            ServiceProvider.objects.create(user=instance)
