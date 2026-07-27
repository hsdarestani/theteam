from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0002_playerevaluation_scores"),
    ]

    operations = [
        migrations.CreateModel(
            name="MatchPerformanceRating",
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
                ("scores", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "performance",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="detailed_rating",
                        to="core.matchperformance",
                    ),
                ),
            ],
            options={
                "verbose_name": "Detaillierte Spielbewertung",
                "verbose_name_plural": "Detaillierte Spielbewertungen",
            },
        ),
    ]
