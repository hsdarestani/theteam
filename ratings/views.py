from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Match, MatchPerformance

from .forms import MatchDetailedPerformanceForm
from .models import MatchPerformanceRating


@login_required
def match_detail(request, pk):
    match = get_object_or_404(Match, pk=pk)
    selected_player_id = request.POST.get("player") or request.GET.get("player")

    editing_performance = None
    if selected_player_id:
        editing_performance = MatchPerformance.objects.filter(
            match=match,
            player_id=selected_player_id,
        ).first()

    detailed_profile = None
    if editing_performance:
        try:
            detailed_profile = editing_performance.detailed_rating
        except MatchPerformanceRating.DoesNotExist:
            detailed_profile = None

    initial = {"player": selected_player_id} if selected_player_id and not editing_performance else {}
    form = MatchDetailedPerformanceForm(
        request.POST or None,
        instance=editing_performance,
        initial=initial,
        stored_scores=detailed_profile.scores if detailed_profile else None,
    )

    if request.method == "POST" and form.is_valid():
        performance = form.save(commit=False)
        performance.match = match
        performance.save()
        MatchPerformanceRating.objects.update_or_create(
            performance=performance,
            defaults={"scores": form.rating_scores},
        )
        messages.success(
            request,
            f"Vollständige Spielbewertung für {performance.player.full_name} gespeichert.",
        )
        return redirect("match_detail", pk=pk)

    performances = list(
        match.performances.select_related("player", "detailed_rating").order_by(
            "player__shirt_number"
        )
    )
    for performance in performances:
        try:
            performance.detailed_profile = performance.detailed_rating
        except MatchPerformanceRating.DoesNotExist:
            performance.detailed_profile = None

    return render(
        request,
        "core/match_detail.html",
        {
            "match": match,
            "performances": performances,
            "form": form,
            "editing_performance": editing_performance,
        },
    )
