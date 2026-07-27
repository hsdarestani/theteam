from django.db import migrations, models


def copy_legacy_scores(apps, schema_editor):
    PlayerEvaluation = apps.get_model("core", "PlayerEvaluation")
    for evaluation in PlayerEvaluation.objects.all().iterator():
        evaluation.scores = {
            "overall": evaluation.performance,
            "mentality": evaluation.mentality,
        }
        evaluation.save(update_fields=["scores"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="playerevaluation",
            name="scores",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(copy_legacy_scores, migrations.RunPython.noop),
    ]
