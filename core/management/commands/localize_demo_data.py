from django.core.management.base import BaseCommand

from core.branding import language_prefix
from core.identity_models import TeamIdentity
from core.models import (
    Attendance,
    MatchPerformance,
    Player,
    PlayerEvaluation,
    TaskAssignment,
    TeamEvent,
    TrainingSession,
)


class Command(BaseCommand):
    help = "Translate only the known fictional German demo dataset for the active language."

    def handle(self, *args, **options):
        identity = TeamIdentity.load()
        if language_prefix(identity.resolved_language) != "fa":
            self.stdout.write("Demo localization skipped: active language is not Persian.")
            return

        updates = 0
        updates += self._replace(
            Player,
            "position",
            {
                "Torwart": "دروازه‌بان",
                "Innenverteidigung": "مدافع میانی",
                "Mittelfeld": "هافبک",
                "Flügel": "وینگر",
                "Sturm": "مهاجم",
                "Rechtsverteidigung": "مدافع راست",
            },
        )
        updates += self._replace(
            Player,
            "nationality",
            {
                "Deutschland": "آلمان",
                "Österreich": "اتریش",
                "Schweiz": "سوئیس",
                "Dänemark": "دانمارک",
                "Portugal": "پرتغال",
            },
        )
        updates += self._replace(
            TeamEvent,
            "title",
            {
                "Teamtraining": "تمرین تیمی",
                "Spielvorbereitung": "آمادگی پیش از بازی",
            },
        )
        updates += self._replace(
            TeamEvent,
            "location",
            {
                "Trainingszentrum": "مرکز تمرین",
                "Besprechungsraum 2": "اتاق جلسه ۲",
            },
        )
        updates += self._replace(
            TrainingSession,
            "title",
            {"Teamtraining": "تمرین تیمی"},
        )
        updates += self._replace(
            TrainingSession,
            "location",
            {"Trainingszentrum": "مرکز تمرین"},
        )
        updates += self._replace(
            TrainingSession,
            "focus",
            {"Pressing, Umschalten, Standards": "پرس، انتقال بازی و ضربات ایستگاهی"},
        )
        updates += self._replace(
            Attendance,
            "comment",
            {"Individuelles Programm": "برنامه انفرادی"},
        )
        updates += self._replace(
            TaskAssignment,
            "task",
            {"Materialcheck mit Athletikteam": "بررسی تجهیزات با تیم بدنسازی"},
        )
        updates += self._replace(
            MatchPerformance,
            "comment",
            {
                "Konzentrierter Auftritt.": "نمایشی متمرکز.",
                "Gute Intensität und klare Aktionen.": "شدت مناسب و عملکردی روشن.",
            },
        )
        updates += self._replace(
            PlayerEvaluation,
            "comment",
            {
                "Stabile Entwicklung im aktuellen Trainingsblock.": "روند پیشرفت باثبات در دوره تمرینی فعلی."
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Localized {updates} demo values for Persian."))

    @staticmethod
    def _replace(model, field_name, replacements):
        changed = 0
        for source, target in replacements.items():
            changed += model.objects.filter(**{field_name: source}).update(**{field_name: target})
        return changed
