from django.contrib import admin
from .models import Attendance, Match, MatchPerformance, Player, PlayerEvaluation, ReportNote, TaskAssignment, TeamEvent, TrainingSession

admin.site.site_header = "Team Performance Administration"
for model in [Player, TeamEvent, TrainingSession, Attendance, TaskAssignment, PlayerEvaluation, Match, MatchPerformance, ReportNote]:
    admin.site.register(model)
