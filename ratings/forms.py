from collections import OrderedDict

from django import forms

from core.models import EVALUATION_CATEGORIES, EVALUATION_GROUPS, MatchPerformance, Player


ATHLETIC_KEYS = ("work_rate", "pace", "stamina", "commitment")


class MatchDetailedPerformanceForm(forms.ModelForm):
    class Meta:
        model = MatchPerformance
        fields = ["player", "minutes_played", "comment"]
        labels = {
            "player": "Spieler",
            "minutes_played": "Spielminuten",
            "comment": "Kurzkommentar",
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Beobachtung, Schlüsselszene oder nächste Maßnahme …",
                }
            )
        }

    def __init__(self, *args, stored_scores=None, **kwargs):
        super().__init__(*args, **kwargs)
        stored_scores = dict(stored_scores or {})

        player_field = self.fields.pop("player")
        minutes_field = self.fields.pop("minutes_played")
        comment_field = self.fields.pop("comment")
        player_field.queryset = Player.objects.filter(active=True)

        fields = OrderedDict()
        fields["player"] = player_field
        fields["minutes_played"] = minutes_field

        for key, label, group_slug, _group_label in EVALUATION_CATEGORIES:
            fields[key] = forms.IntegerField(
                label=label,
                min_value=1,
                max_value=10,
                initial=self.initial.get(key, stored_scores.get(key, self._legacy_default(key))),
                widget=forms.NumberInput(
                    attrs={
                        "type": "range",
                        "min": 1,
                        "max": 10,
                        "step": 1,
                        "data-rating-group": group_slug,
                    }
                ),
            )

        fields["comment"] = comment_field
        self.fields = fields
        self._apply_styles()
        self.rating_scores = {}

    def _legacy_default(self, key):
        if not self.instance or not self.instance.pk:
            return 7
        if key == "overall":
            return self.instance.performance
        if key == "mentality":
            return self.instance.mentality
        if key in ATHLETIC_KEYS:
            return self.instance.physicality
        return 7

    def _apply_styles(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    @property
    def grouped_fields(self):
        return [
            {
                "slug": slug,
                "label": label,
                "fields": [self[key] for key, _category_label in categories],
            }
            for slug, label, categories in EVALUATION_GROUPS
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        scores = {
            key: self.cleaned_data[key]
            for key, _label, _group_slug, _group_label in EVALUATION_CATEGORIES
        }
        instance.performance = scores["overall"]
        instance.mentality = scores["mentality"]
        instance.physicality = round(
            sum(scores[key] for key in ATHLETIC_KEYS) / len(ATHLETIC_KEYS)
        )
        self.rating_scores = scores
        if commit:
            instance.save()
        return instance
