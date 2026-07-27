from django.urls import path

from ratings import views as rating_views

from . import management_views, views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("setup/", views.setup, name="setup"),
    path("", views.dashboard, name="dashboard"),
    path("spieler/", management_views.player_list, name="players"),
    path("spieler/neu/", views.player_create, name="player_create"),
    path("spieler/<int:pk>/", views.player_detail, name="player_detail"),
    path("spieler/<int:pk>/bewerten/", views.evaluate_player, name="evaluate_player"),
    path("training/", views.training_list, name="trainings"),
    path("training/neu/", views.training_create, name="training_create"),
    path("training/<int:pk>/", views.training_detail, name="training_detail"),
    path("kalender/", views.calendar_view, name="calendar"),
    path("kalender/neu/", views.event_create, name="event_create"),
    path("kalender/<int:pk>/bearbeiten/", management_views.event_edit, name="event_edit"),
    path("spiele/", views.match_list, name="matches"),
    path("spiele/neu/", views.match_create, name="match_create"),
    path("spiele/<int:pk>/", rating_views.match_detail, name="match_detail"),
    path("report/", management_views.report, name="report"),
]
