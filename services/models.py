from django.db import models
from django.conf import settings

# Import ServiceProvider from accounts app
from accounts.models import ServiceProvider


class Service(models.Model):
    """Main service categories (Plumbing, Cleaning, Electrical, etc.)"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -----------------------------
# SAFE DEFAULT SERVICE HANDLER
# -----------------------------
def default_service():
    """
    Ensures the ServiceRequest model always has a valid service ID.
    If no service exists, automatically create a fallback.
    """
    service = Service.objects.first()
    if service:
        return service.id
    return Service.objects.create(name="General Service").id


class ServiceRequest(models.Model):
    """Requests made by homeowners to providers"""

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    homeowner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="homeowner_requests",
    )

    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name="provider_requests",
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="service_requests",
        default=default_service,
    )

    description = models.TextField(
        default="No description provided",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request {self.id} - {self.homeowner.username} → {self.provider.user.username}"
