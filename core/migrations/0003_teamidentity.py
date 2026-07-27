from django.db import migrations, models


def create_default_identity(apps, schema_editor):
    TeamIdentity = apps.get_model("core", "TeamIdentity")
    TeamIdentity.objects.get_or_create(
        pk=1,
        defaults={
            "team_name": "The Team",
            "short_name": "TEAM",
            "app_name": "Performance Hub",
            "tagline": "Training, Kader und Leistung auf einen Blick.",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_playerevaluation_scores"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamIdentity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("team_name", models.CharField(default="The Team", max_length=120)),
                ("short_name", models.CharField(default="TEAM", max_length=40)),
                ("app_name", models.CharField(default="Performance Hub", max_length=120)),
                (
                    "tagline",
                    models.CharField(
                        blank=True,
                        default="Training, Kader und Leistung auf einen Blick.",
                        max_length=240,
                    ),
                ),
                ("logo", models.FileField(blank=True, upload_to="team_identity/")),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("de", "Deutsch"),
                            ("en", "English"),
                            ("ar", "العربية"),
                            ("fa", "فارسی"),
                            ("custom", "Custom language"),
                        ],
                        default="de",
                        max_length=10,
                    ),
                ),
                (
                    "custom_language_code",
                    models.CharField(
                        blank=True,
                        help_text="Used only when Custom language is selected, for example fr, es or tr.",
                        max_length=12,
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[
                            ("auto", "Automatic"),
                            ("ltr", "Left to right"),
                            ("rtl", "Right to left"),
                        ],
                        default="auto",
                        max_length=4,
                    ),
                ),
                ("primary_color", models.CharField(default="#e41e2b", max_length=7)),
                ("primary_dark_color", models.CharField(default="#bd111d", max_length=7)),
                ("secondary_color", models.CharField(default="#111216", max_length=7)),
                ("background_color", models.CharField(default="#f4f5f7", max_length=7)),
                ("surface_color", models.CharField(default="#ffffff", max_length=7)),
                ("text_color", models.CharField(default="#17181c", max_length=7)),
                (
                    "custom_translations",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Optional phrase overrides, for example: {"Übersicht": "Accueil"}.',
                    ),
                ),
                (
                    "custom_css",
                    models.TextField(
                        blank=True,
                        help_text="Optional advanced CSS overrides. Only administrators should edit this field.",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Team identity",
                "verbose_name_plural": "Team identity",
            },
        ),
        migrations.RunPython(create_default_identity, migrations.RunPython.noop),
    ]
