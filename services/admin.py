from django.contrib import admin
from .models import Service, ServiceRequest

# -------------------------
# Service Admin
# -------------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


# -------------------------
# ServiceRequest Admin
# -------------------------
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

    # -------------------------
    # Bulk actions for status
    # -------------------------
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

    actions = [mark_as_pending, mark_as_accepted, mark_as_completed, mark_as_cancelled]
