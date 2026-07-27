from __future__ import annotations

import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models

from .branding import RTL_LANGUAGES, language_prefix


class TeamIdentity(models.Model):
    class Language(models.TextChoices):
        GERMAN = "de", "Deutsch"
        ENGLISH = "en", "English"
        ARABIC = "ar", "العربية"
        PERSIAN = "fa", "فارسی"
        CUSTOM = "custom", "Custom language"

    class Direction(models.TextChoices):
        AUTO = "auto", "Automatic"
        LTR = "ltr", "Left to right"
        RTL = "rtl", "Right to left"

    team_name = models.CharField(max_length=120, default="The Team")
    short_name = models.CharField(max_length=40, default="TEAM")
    app_name = models.CharField(max_length=120, default="Performance Hub")
    tagline = models.CharField(
        max_length=240,
        default="Training, Kader und Leistung auf einen Blick.",
        blank=True,
    )
    logo = models.FileField(upload_to="team_identity/", blank=True)

    language = models.CharField(max_length=10, choices=Language.choices, default=Language.GERMAN)
    custom_language_code = models.CharField(
        max_length=12,
        blank=True,
        help_text="Used only when Custom language is selected, for example fr, es or tr.",
    )
    direction = models.CharField(max_length=4, choices=Direction.choices, default=Direction.AUTO)

    primary_color = models.CharField(max_length=7, default="#e41e2b")
    primary_dark_color = models.CharField(max_length=7, default="#bd111d")
    secondary_color = models.CharField(max_length=7, default="#111216")
    background_color = models.CharField(max_length=7, default="#f4f5f7")
    surface_color = models.CharField(max_length=7, default="#ffffff")
    text_color = models.CharField(max_length=7, default="#17181c")

    custom_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Optional phrase overrides, for example: {"Übersicht": "Accueil"}.',
    )
    custom_css = models.TextField(
        blank=True,
        help_text="Optional advanced CSS overrides. Only administrators should edit this field.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        verbose_name = "Team identity"
        verbose_name_plural = "Team identity"

    def __str__(self):
        return self.team_name

    def clean(self):
        super().clean()
        errors = {}
        for field_name in (
            "primary_color",
            "primary_dark_color",
            "secondary_color",
            "background_color",
            "surface_color",
            "text_color",
        ):
            value = getattr(self, field_name, "")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", value or ""):
                errors[field_name] = "Enter a six-digit hex color such as #0b6b3a."

        if self.language == self.Language.CUSTOM and not self.custom_language_code.strip():
            errors["custom_language_code"] = "Enter a language code for the custom language."

        if self.logo:
            extension = Path(self.logo.name).suffix.lower()
            if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
                errors["logo"] = "Upload a PNG, JPG, JPEG or WebP image."
            if getattr(self.logo, "size", 0) > 5 * 1024 * 1024:
                errors["logo"] = "The logo must be smaller than 5 MB."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # The identity is a true singleton: creating another instance replaces
        # the single row instead of failing primary-key validation.
        self.pk = 1
        self.full_clean(exclude=[self._meta.pk.name])
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return None

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def resolved_language(self):
        if self.language == self.Language.CUSTOM and self.custom_language_code.strip():
            return self.custom_language_code.strip().lower()
        return self.language

    @property
    def resolved_direction(self):
        if self.direction != self.Direction.AUTO:
            return self.direction
        return "rtl" if language_prefix(self.resolved_language) in RTL_LANGUAGES else "ltr"
