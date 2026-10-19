from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "owner", "status", "page_count", "created_at")
    list_filter = ("status",)
    search_fields = ("original_filename", "owner__username")
