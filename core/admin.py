from django import forms
from django.contrib import admin
from django.shortcuts import redirect

from .identity_models import TeamIdentity
from .models import (
    Attendance,
    Match,
    MatchPerformance,
    Player,
    PlayerEvaluation,
    ReportNote,
    TaskAssignment,
    TeamEvent,
    TrainingSession,
)


class TeamIdentityAdminForm(forms.ModelForm):
    class Meta:
        model = TeamIdentity
        fields = "__all__"
        widgets = {
            "primary_color": forms.TextInput(attrs={"type": "color"}),
            "primary_dark_color": forms.TextInput(attrs={"type": "color"}),
            "secondary_color": forms.TextInput(attrs={"type": "color"}),
            "background_color": forms.TextInput(attrs={"type": "color"}),
            "surface_color": forms.TextInput(attrs={"type": "color"}),
            "text_color": forms.TextInput(attrs={"type": "color"}),
            "custom_css": forms.Textarea(attrs={"rows": 12, "class": "vLargeTextField"}),
            "custom_translations": forms.Textarea(attrs={"rows": 14, "class": "vLargeTextField"}),
        }


@admin.register(TeamIdentity)
class TeamIdentityAdmin(admin.ModelAdmin):
    form = TeamIdentityAdminForm
    readonly_fields = ("updated_at",)
    fieldsets = (
        (
            "Team and product identity",
            {"fields": ("team_name", "short_name", "app_name", "tagline", "logo")},
        ),
        (
            "Language and direction",
            {"fields": ("language", "custom_language_code", "direction", "custom_translations")},
        ),
        (
            "Brand colors",
            {
                "fields": (
                    "primary_color",
                    "primary_dark_color",
                    "secondary_color",
                    "background_color",
                    "surface_color",
                    "text_color",
                )
            },
        ),
        (
            "Advanced",
            {"classes": ("collapse",), "fields": ("custom_css", "updated_at")},
        ),
    )

    def changelist_view(self, request, extra_context=None):
        identity = TeamIdentity.load()
        return redirect("admin:core_teamidentity_change", identity.pk)

    def has_add_permission(self, request):
        return not TeamIdentity.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = "The Team Administration"
admin.site.site_title = "The Team Admin"
admin.site.index_title = "Team management"

for model in [
    Player,
    TeamEvent,
    TrainingSession,
    Attendance,
    TaskAssignment,
    PlayerEvaluation,
    Match,
    MatchPerformance,
    ReportNote,
]:
    admin.site.register(model)
