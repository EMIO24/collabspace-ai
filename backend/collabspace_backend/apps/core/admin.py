from django.contrib import admin
from django.db import models as django_models
from .models import *

# Example admin action
def mark_as_active(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} items marked as active.")

mark_as_active.short_description = "Mark selected items as active"

# Iterate over a copy of globals()
for name, model in list(globals().items()):
    if isinstance(model, type) and issubclass(model, django_models.Model):
        # Skip abstract models
        if getattr(model._meta, "abstract", False):
            continue
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass
