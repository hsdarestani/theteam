from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import EVALUATION_CATEGORIES, Match, MatchPerformance, Player
from core.views import seed_demo_data

from .models import MatchPerformanceRating


class UnifiedMatchRatingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            "matchcoach",
            "matchcoach@example.com",
            "SecureCoach!2026",
            first_name="Match",
        )
        seed_demo_data(self.user)
        self.client.force_login(self.user)
        self.match = Match.objects.first()

    def test_match_page_uses_all_shared_categories(self):
        response = self.client.get(reverse("match_detail", args=[self.match.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "30 Kriterien · einheitlich mit dem Kaderprofil")
        self.assertContains(response, "Gesamtleistung")
        self.assertContains(response, "Spielintelligenz")
        self.assertContains(response, "Man of the Match")
        self.assertEqual(response.content.decode().count('type="range"'), len(EVALUATION_CATEGORIES))

    def test_match_rating_saves_full_profile_and_summary_fields(self):
        player = Player.objects.order_by("shirt_number").last()
        payload = {
            key: 8
            for key, _label, _group_slug, _group_label in EVALUATION_CATEGORIES
        }
        payload.update(
            {
                "player": player.pk,
                "minutes_played": 73,
                "mentality": 9,
                "work_rate": 6,
                "pace": 7,
                "stamina": 8,
                "commitment": 9,
                "comment": "Komplette Bewertung im Spielkontext.",
            }
        )

        response = self.client.post(reverse("match_detail", args=[self.match.pk]), payload)
        self.assertRedirects(response, reverse("match_detail", args=[self.match.pk]))

        performance = MatchPerformance.objects.get(match=self.match, player=player)
        profile = MatchPerformanceRating.objects.get(performance=performance)
        self.assertEqual(len(profile.scores), len(EVALUATION_CATEGORIES))
        self.assertEqual(performance.performance, 8)
        self.assertEqual(performance.mentality, 9)
        self.assertEqual(performance.physicality, 8)
        self.assertEqual(profile.scores["decision_making"], 8)

    def test_existing_match_rating_can_be_opened_for_editing(self):
        performance = MatchPerformance.objects.filter(match=self.match).first()
        response = self.client.get(
            reverse("match_detail", args=[self.match.pk]),
            {"player": performance.player_id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BEWERTUNG BEARBEITEN")
        self.assertContains(response, "Bewertung aktualisieren")
