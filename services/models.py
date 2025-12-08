from django.conf import settings
from django.db import models
from accounts.models import ServiceProvider, Service

class ServiceRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    homeowner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_requests')
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='requests')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request {self.id} by {self.homeowner.username} -> {self.provider.user.username} ({self.status})"
