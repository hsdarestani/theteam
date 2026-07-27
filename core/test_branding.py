import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .html_translation import translate_html_content
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
        self.assertContains(response, "css/rtl.css")

    def test_custom_translation_override_is_applied(self):
        identity = TeamIdentity.load()
        identity.custom_translations = {"Übersicht": "Accueil personnalisé"}
        identity.save()

        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Accueil personnalisé")

    def test_translation_does_not_corrupt_compounds_or_user_content(self):
        html = '<strong translate="no">Spielvorbereitung</strong><span>Spiel</span>'
        translated = translate_html_content(html, "ar")

        self.assertIn("Spielvorbereitung", translated)
        self.assertIn("مباراة", translated)
        self.assertNotIn("مباراةvorbereitung", translated)

    def test_admin_can_upload_and_read_a_team_logo(self):
        # FileField validation only needs a correctly named uploaded file; the
        # PNG header keeps this fixture representative without adding binaries.
        logo = SimpleUploadedFile(
            "al-nassr.png",
            b"\x89PNG\r\n\x1a\nlogo-test-payload",
            content_type="image/png",
        )
        with tempfile.TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("admin:core_teamidentity_change", args=[1]),
                {
                    "team_name": "نادي النصر السعودي",
                    "short_name": "النصر",
                    "app_name": "منصة أداء النصر",
                    "tagline": "إدارة الفريق والأداء في مكان واحد",
                    "logo": logo,
                    "language": TeamIdentity.Language.ARABIC,
                    "custom_language_code": "",
                    "direction": TeamIdentity.Direction.RTL,
                    "primary_color": "#f9d616",
                    "primary_dark_color": "#d1a900",
                    "secondary_color": "#123c73",
                    "background_color": "#f5f6f8",
                    "surface_color": "#ffffff",
                    "text_color": "#13213c",
                    "custom_translations": "{}",
                    "custom_css": "",
                    "_continue": "1",
                },
            )

            self.assertEqual(response.status_code, 302)
            identity = TeamIdentity.load()
            self.assertTrue(identity.logo.name.endswith("al-nassr.png"))

            logo_response = self.client.get(reverse("team_logo"))
            self.assertEqual(logo_response.status_code, 200)
            self.assertEqual(logo_response["Content-Type"], "image/png")
            logo_response.close()

    def test_admin_identity_list_redirects_to_singleton_change_form(self):
        response = self.client.get(reverse("admin:core_teamidentity_changelist"))
        self.assertRedirects(
            response,
            reverse("admin:core_teamidentity_change", args=[1]),
            fetch_redirect_response=False,
        )
