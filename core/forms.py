from collections import OrderedDict

from django import forms
from django.contrib.auth import get_user_model

from .models import (
    EVALUATION_CATEGORIES,
    EVALUATION_GROUPS,
    Match,
    MatchPerformance,
    Player,
    PlayerEvaluation,
    ReportNote,
    TaskAssignment,
    TeamEvent,
    TrainingSession,
)

DT_INPUT = forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")


class StyledFormMixin:
    def apply_styles(self):
        for field in self.fields.values():
            cls = "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                cls = "form-check-input"
            field.widget.attrs["class"] = cls


class SetupForm(forms.Form, StyledFormMixin):
    first_name = forms.CharField(label="Vorname", max_length=80)
    last_name = forms.CharField(label="Nachname", max_length=80)
    username = forms.CharField(label="Benutzername", max_length=80)
    password = forms.CharField(label="Sicheres Passwort", widget=forms.PasswordInput, min_length=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def save(self):
        User = get_user_model()
        return User.objects.create_superuser(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
        )


class PlayerForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = Player
        fields = ["first_name", "last_name", "shirt_number", "position", "status", "birth_date", "nationality", "notes"]
        labels = {
            "first_name": "Vorname",
            "last_name": "Nachname",
            "shirt_number": "Rückennummer",
            "position": "Position",
            "status": "Status",
            "birth_date": "Geburtsdatum",
            "nationality": "Nationalität",
            "notes": "Interne Notiz",
        }
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


class EvaluationForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = PlayerEvaluation
        fields = ["comment"]
        labels = {"comment": "Kommentar des Trainers"}
        widgets = {"comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Kurze Beobachtung, Entwicklung oder nächste Maßnahme …"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stored_scores = self.instance.normalized_scores if self.instance and self.instance.pk else {}
        comment_field = self.fields.pop("comment")

        rating_fields = OrderedDict()
        for key, label, group_slug, _group_label in EVALUATION_CATEGORIES:
            rating_fields[key] = forms.IntegerField(
                label=label,
                min_value=1,
                max_value=10,
                initial=self.initial.get(key, stored_scores.get(key, 7)),
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

        rating_fields["comment"] = comment_field
        self.fields = rating_fields
        self.apply_styles()

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
        scores = {key: self.cleaned_data[key] for key, _label, _group_slug, _group_label in EVALUATION_CATEGORIES}
        instance.scores = scores
        instance.performance = scores["overall"]
        instance.mentality = scores["mentality"]

        athletic_keys = ("work_rate", "pace", "stamina", "commitment")
        instance.physicality = round(sum(scores[key] for key in athletic_keys) / len(athletic_keys))

        if commit:
            instance.save()
        return instance


class TrainingForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = TrainingSession
        fields = ["title", "starts_at", "ends_at", "location", "focus", "status", "notes"]
        labels = {
            "title": "Titel",
            "starts_at": "Start",
            "ends_at": "Ende",
            "location": "Ort",
            "focus": "Trainingsfokus",
            "status": "Status",
            "notes": "Notizen",
        }
        widgets = {"starts_at": DT_INPUT, "ends_at": DT_INPUT, "notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]


class EventForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = TeamEvent
        fields = ["title", "event_type", "starts_at", "ends_at", "location", "notes"]
        labels = {"title": "Titel", "event_type": "Art", "starts_at": "Start", "ends_at": "Ende", "location": "Ort", "notes": "Notizen"}
        widgets = {"starts_at": DT_INPUT, "ends_at": DT_INPUT, "notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]


class MatchForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = Match
        fields = ["opponent", "kickoff", "competition", "location", "venue", "goals_for", "goals_against", "notes"]
        labels = {
            "opponent": "Gegner",
            "kickoff": "Anstoß",
            "competition": "Wettbewerb",
            "location": "Ort",
            "venue": "Spielort",
            "goals_for": "Eigene Tore",
            "goals_against": "Gegentore",
            "notes": "Spielnotizen",
        }
        widgets = {"kickoff": DT_INPUT, "notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["kickoff"].input_formats = ["%Y-%m-%dT%H:%M"]


class MatchPerformanceForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = MatchPerformance
        fields = ["player", "minutes_played", "mentality", "physicality", "performance", "comment"]
        labels = {
            "player": "Spieler",
            "minutes_played": "Spielminuten",
            "mentality": "Mentalität",
            "physicality": "Physis",
            "performance": "Leistung",
            "comment": "Kurzkommentar",
        }
        widgets = {
            key: forms.NumberInput(attrs={"type": "range", "min": 1, "max": 10, "step": 1})
            for key in ["mentality", "physicality", "performance"]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["player"].queryset = Player.objects.filter(active=True)


class TaskForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = TaskAssignment
        fields = ["player", "task"]
        labels = {"player": "Spieler", "task": "Aufgabe"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["player"].queryset = Player.objects.filter(active=True)


class ReportNoteForm(forms.ModelForm, StyledFormMixin):
    class Meta:
        model = ReportNote
        fields = ["note"]
        labels = {"note": "Kommentar zum Report"}
        widgets = {"note": forms.Textarea(attrs={"rows": 4, "placeholder": "Interne Einschätzung oder Hinweise für den Ausdruck …"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
