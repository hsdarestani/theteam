from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .identity_models import TeamIdentity


class TeamIdentityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="safe-test-password-123",
        )
        self.client.force_login(self.user)

    def test_identity_is_singleton(self):
        first = TeamIdentity.load()
        first.team_name = "First Team"
        first.save()

        second = TeamIdentity(team_name="Replacement Team")
        second.save()

        self.assertEqual(TeamIdentity.objects.count(), 1)
        self.assertEqual(TeamIdentity.load().team_name, "Replacement Team")

    def test_arabic_branding_changes_direction_colors_and_labels(self):
        identity = TeamIdentity.load()
        identity.team_name = "النادي الأهلي"
        identity.short_name = "الأهلي"
        identity.language = TeamIdentity.Language.ARABIC
        identity.primary_color = "#0b6b3a"
        identity.primary_dark_color = "#064528"
        identity.save()

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, 'lang="ar"')
        self.assertContains(response, 'dir="rtl"')
        self.assertContains(response, "النادي الأهلي")
        self.assertContains(response, "#0b6b3a")
        self.assertContains(response, "لوحة التحكم")

    def test_custom_translation_override_is_applied(self):
        identity = TeamIdentity.load()
        identity.custom_translations = {"Übersicht": "Accueil personnalisé"}
        identity.save()

        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Accueil personnalisé")

    def test_admin_identity_list_redirects_to_singleton_change_form(self):
        response = self.client.get(reverse("admin:core_teamidentity_changelist"))
        self.assertRedirects(
            response,
            reverse("admin:core_teamidentity_change", args=[1]),
            fetch_redirect_response=False,
        )
