from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import EventForm, ReportNoteForm
from .models import Match, Player, PlayerEvaluation, ReportNote, TeamEvent, TrainingSession


POSITION_GROUPS = (
    ("goalkeeper", "Torwart", ("torwart", "keeper")),
    ("defense", "Abwehr", ("verteid", "abwehr", "defens")),
    ("midfield", "Mittelfeld", ("mittelfeld", "zentrum", "sechser", "achter", "zehner")),
    ("attack", "Sturm", ("sturm", "flügel", "angriff", "offens")),
    ("other", "Weitere", ()),
)
POSITION_GROUP_INDEX = {key: index for index, (key, _label, _tokens) in enumerate(POSITION_GROUPS)}
REPORT_TYPES = (
    ("overview", "Teamübersicht"),
    ("player", "Spielerreport"),
    ("match", "Spielbericht"),
    ("training", "Trainingsreport"),
)


def _position_group(position):
    value = (position or "").casefold()
    for key, label, tokens in POSITION_GROUPS[:-1]:
        if any(token in value for token in tokens):
            return key, label
    return "other", "Weitere"


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@login_required
def player_list(request):
    q = request.GET.get("q", "").strip()
    position_filter = request.GET.get("position", "all")
    sort = request.GET.get("sort", "position")
    rating_filter = request.GET.get("rating", "all")

    queryset = Player.objects.filter(active=True).annotate(
        avg_performance=Avg("evaluations__performance"),
        avg_mentality=Avg("evaluations__mentality"),
        avg_physicality=Avg("evaluations__physicality"),
    )
    if q:
        queryset = queryset.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(position__icontains=q)
            | Q(shirt_number__icontains=q)
        )

    players = list(queryset)
    for player in players:
        group_key, group_label = _position_group(player.position)
        player.position_group_key = group_key
        player.position_group_label = group_label

    if position_filter != "all":
        players = [player for player in players if player.position_group_key == position_filter]

    rated_players = [player for player in players if player.avg_performance is not None]
    if rating_filter == "top":
        players = sorted(
            rated_players,
            key=lambda player: (-float(player.avg_performance), player.shirt_number),
        )[:5]
        sort = "rating_desc"
    elif rating_filter == "bottom":
        players = sorted(
            rated_players,
            key=lambda player: (float(player.avg_performance), player.shirt_number),
        )[:5]
        sort = "rating_asc"
    elif sort == "number":
        players.sort(key=lambda player: player.shirt_number)
    elif sort == "rating_desc":
        players.sort(
            key=lambda player: (
                player.avg_performance is None,
                -(float(player.avg_performance) if player.avg_performance is not None else 0),
                player.shirt_number,
            )
        )
    elif sort == "rating_asc":
        players.sort(
            key=lambda player: (
                player.avg_performance is None,
                float(player.avg_performance) if player.avg_performance is not None else 0,
                player.shirt_number,
            )
        )
    else:
        sort = "position"
        players.sort(
            key=lambda player: (
                POSITION_GROUP_INDEX[player.position_group_key],
                player.shirt_number,
            )
        )

    player_sections = []
    if sort == "position" and rating_filter == "all":
        for key, label, _tokens in POSITION_GROUPS:
            section_players = [player for player in players if player.position_group_key == key]
            if section_players:
                player_sections.append({"key": key, "label": label, "players": section_players})

    return render(
        request,
        "core/player_list.html",
        {
            "players": players,
            "player_sections": player_sections,
            "q": q,
            "position_filter": position_filter,
            "sort": sort,
            "rating_filter": rating_filter,
            "position_groups": POSITION_GROUPS[:-1],
            "result_count": len(players),
        },
    )


@login_required
def event_edit(request, pk):
    event = get_object_or_404(TeamEvent, pk=pk)
    form = EventForm(request.POST or None, instance=event)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        if not event.created_by_id:
            event.created_by = request.user
        event.save()
        messages.success(request, "Termin wurde aktualisiert.")
        local_start = event.starts_at.astimezone()
        return redirect(f"{reverse('calendar')}?year={local_start.year}&month={local_start.month}")
    return render(
        request,
        "core/form_page.html",
        {
            "form": form,
            "title": "Termin bearbeiten",
            "eyebrow": "Kalender",
            "submit_label": "Änderungen speichern",
            "cancel_url": "calendar",
        },
    )


@login_required
def report(request):
    report_type = request.GET.get("type", "overview")
    if report_type not in {key for key, _label in REPORT_TYPES}:
        report_type = "overview"

    q = request.GET.get("q", "").strip()
    date_from_value = request.GET.get("date_from", "")
    date_to_value = request.GET.get("date_to", "")
    date_from = _parse_date(date_from_value)
    date_to = _parse_date(date_to_value)
    selected_player_id = _parse_int(request.GET.get("player"))
    selected_match_id = _parse_int(request.GET.get("match"))

    note = ReportNote.objects.first() or ReportNote.objects.create(updated_by=request.user)
    note_form = ReportNoteForm(request.POST or None, instance=note)
    if request.method == "POST" and note_form.is_valid():
        note = note_form.save(commit=False)
        note.updated_by = request.user
        note.save()
        messages.success(request, "Report-Kommentar gespeichert.")
        target = reverse("report")
        query_string = request.GET.urlencode()
        return redirect(f"{target}?{query_string}" if query_string else target)

    training_qs = TrainingSession.objects.all().order_by("-starts_at")
    match_qs = Match.objects.all().order_by("-kickoff")
    evaluation_qs = PlayerEvaluation.objects.select_related("player").all()

    if date_from:
        training_qs = training_qs.filter(starts_at__date__gte=date_from)
        match_qs = match_qs.filter(kickoff__date__gte=date_from)
        evaluation_qs = evaluation_qs.filter(evaluated_at__date__gte=date_from)
    if date_to:
        training_qs = training_qs.filter(starts_at__date__lte=date_to)
        match_qs = match_qs.filter(kickoff__date__lte=date_to)
        evaluation_qs = evaluation_qs.filter(evaluated_at__date__lte=date_to)

    player_q = Q()
    if q:
        training_qs = training_qs.filter(
            Q(title__icontains=q)
            | Q(location__icontains=q)
            | Q(focus__icontains=q)
            | Q(notes__icontains=q)
        )
        match_qs = match_qs.filter(
            Q(opponent__icontains=q)
            | Q(competition__icontains=q)
            | Q(location__icontains=q)
            | Q(notes__icontains=q)
        )
        player_q = (
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(position__icontains=q)
            | Q(shirt_number__icontains=q)
        )
        evaluation_qs = evaluation_qs.filter(
            Q(player__first_name__icontains=q)
            | Q(player__last_name__icontains=q)
            | Q(player__position__icontains=q)
        )

    players_options = Player.objects.filter(active=True).order_by("shirt_number")
    matches_options = Match.objects.all().order_by("-kickoff")[:100]

    selected_player = None
    if selected_player_id:
        selected_player = get_object_or_404(Player, pk=selected_player_id, active=True)
        evaluation_qs = evaluation_qs.filter(player=selected_player)

    selected_match = None
    if selected_match_id:
        selected_match = match_qs.filter(pk=selected_match_id).first()
    if selected_match is None and report_type in {"overview", "match"}:
        selected_match = match_qs.first()

    evaluation_filter = Q(evaluations__isnull=False)
    if date_from:
        evaluation_filter &= Q(evaluations__evaluated_at__date__gte=date_from)
    if date_to:
        evaluation_filter &= Q(evaluations__evaluated_at__date__lte=date_to)

    report_players_qs = Player.objects.filter(active=True)
    if player_q:
        report_players_qs = report_players_qs.filter(player_q)
    report_players = list(
        report_players_qs.annotate(
            avg_mentality=Avg("evaluations__mentality", filter=evaluation_filter),
            avg_physicality=Avg("evaluations__physicality", filter=evaluation_filter),
            avg_performance=Avg("evaluations__performance", filter=evaluation_filter),
        ).order_by("-avg_performance", "shirt_number")
    )

    team_avg = evaluation_qs.aggregate(
        mentality=Avg("mentality"),
        physicality=Avg("physicality"),
        performance=Avg("performance"),
    )
    recent_training = list(training_qs[:20])
    filtered_matches = list(match_qs[:20])
    selected_player_evaluations = (
        list(evaluation_qs.filter(player=selected_player)[:20]) if selected_player else []
    )
    selected_player_matches = (
        list(
            selected_player.match_performances.select_related("match")
            .filter(match__in=match_qs)
            .order_by("-match__kickoff")[:20]
        )
        if selected_player
        else []
    )

    if report_type == "player":
        report_title = (
            f"Spielerreport · {selected_player.full_name}"
            if selected_player
            else "Spielerreports"
        )
        report_subtitle = "Individuelle Entwicklung, Einsätze und Trainerbewertungen."
    elif report_type == "match":
        report_title = (
            f"Spielbericht · vs. {selected_match.opponent}"
            if selected_match
            else "Spielberichte"
        )
        report_subtitle = "Ergebnis und individuelle Leistungen im gewählten Spiel."
    elif report_type == "training":
        report_title = "Trainingsreport"
        report_subtitle = "Gefilterte Einheiten, Schwerpunkte und Status."
    else:
        report_title = "Team Performance Report"
        report_subtitle = "Überblick über Team, Training und den relevanten Spieltag."

    return render(
        request,
        "core/report.html",
        {
            "note_form": note_form,
            "note": note,
            "report_types": REPORT_TYPES,
            "report_type": report_type,
            "q": q,
            "date_from": date_from_value,
            "date_to": date_to_value,
            "players_options": players_options,
            "matches_options": matches_options,
            "selected_player_id": selected_player_id,
            "selected_match_id": selected_match_id,
            "selected_player": selected_player,
            "selected_match": selected_match,
            "selected_player_evaluations": selected_player_evaluations,
            "selected_player_matches": selected_player_matches,
            "report_players": report_players,
            "recent_training": recent_training,
            "filtered_matches": filtered_matches,
            "team_avg": team_avg,
            "report_title": report_title,
            "report_subtitle": report_subtitle,
        },
    )
