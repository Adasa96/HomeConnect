from django.contrib import admin
from .models import Service, ServiceProvider, ServiceRequest


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "company_name",
        "phone",
        "bio",
        "created_at",  # You need to add this field in ServiceProvider model
    )
    search_fields = ("company_name", "user__username", "phone", "bio")
    filter_horizontal = ("services",)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "homeowner",
        "provider",
        "service",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "homeowner__username",
        "provider__company_name",
        "service__name",
    )

    # Actions to bulk update request status
    def mark_as_pending(self, request, queryset):
        queryset.update(status=ServiceRequest.STATUS_PENDING)
    mark_as_pending.short_description = "Mark selected requests as Pending"

    def mark_as_accepted(self, request, queryset):
        queryset.update(status=ServiceRequest.STATUS_ACCEPTED)
    mark_as_accepted.short_description = "Mark selected requests as Accepted"

    def mark_as_completed(self, request, queryset):
        queryset.update(status=ServiceRequest.STATUS_COMPLETED)
    mark_as_completed.short_description = "Mark selected requests as Completed"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=ServiceRequest.STATUS_CANCELLED)
    mark_as_cancelled.short_description = "Mark selected requests as Cancelled"
