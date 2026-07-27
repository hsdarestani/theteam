from django.db import models

from core.models import EVALUATION_CATEGORY_KEYS, EVALUATION_GROUPS, MatchPerformance


class MatchPerformanceRating(models.Model):
    performance = models.OneToOneField(
        MatchPerformance,
        on_delete=models.CASCADE,
        related_name="detailed_rating",
    )
    scores = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Detaillierte Spielbewertung"
        verbose_name_plural = "Detaillierte Spielbewertungen"

    @property
    def normalized_scores(self):
        values = dict(self.scores or {})
        values.setdefault("overall", self.performance.performance)
        values.setdefault("mentality", self.performance.mentality)
        return values

    @property
    def overall(self):
        return self.normalized_scores.get("overall", self.performance.performance)

    @property
    def detailed_average(self):
        values = [
            float(value)
            for key, value in self.normalized_scores.items()
            if key in EVALUATION_CATEGORY_KEYS and value is not None
        ]
        return round(sum(values) / len(values), 1) if values else self.performance.average

    @property
    def grouped_scores(self):
        values = self.normalized_scores
        groups = []
        for slug, label, categories in EVALUATION_GROUPS:
            items = [
                {"key": key, "label": category_label, "value": values.get(key)}
                for key, category_label in categories
            ]
            present = [float(item["value"]) for item in items if item["value"] is not None]
            groups.append(
                {
                    "slug": slug,
                    "label": label,
                    "items": items,
                    "average": round(sum(present) / len(present), 1) if present else None,
                }
            )
        return groups

    def __str__(self):
        return f"{self.performance.player} · {self.performance.match}"
