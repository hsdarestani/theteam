from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .html_translation import translate_html_content
from .identity_models import TeamIdentity
from .models import TeamEvent


class PersianLocalizationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="persian-admin",
            email="persian@example.com",
            password="safe-test-password-123",
        )
        self.client.force_login(self.user)
        identity = TeamIdentity.load()
        identity.language = TeamIdentity.Language.PERSIAN
        identity.direction = TeamIdentity.Direction.RTL
        identity.save()

    def test_safe_attributes_are_translated_but_input_values_are_preserved(self):
        html = (
            '<input placeholder="Name, Position oder Nummer" value="Spielvorbereitung">'
            '<a aria-label="Nächster Monat" title="Termin bearbeiten">Weiter</a>'
        )
        translated = translate_html_content(html, "fa")

        self.assertIn('placeholder="نام، پست یا شماره"', translated)
        self.assertIn('aria-label="ماه بعد"', translated)
        self.assertIn('title="ویرایش رویداد"', translated)
        self.assertIn('value="Spielvorbereitung"', translated)

    def test_persian_event_edit_is_fully_localized(self):
        event = TeamEvent.objects.create(
            title="Spielvorbereitung",
            event_type="meeting",
            starts_at=timezone.now(),
            location="Besprechungsraum 2",
            created_by=self.user,
        )
        call_command("localize_demo_data", verbosity=0)
        event.refresh_from_db()

        response = self.client.get(reverse("event_edit", args=[event.pk]))

        for phrase in (
            'lang="fa"',
            'dir="rtl"',
            "ویرایش رویداد",
            "فقط اطلاعاتی را ثبت کن که مربی واقعاً به آن‌ها نیاز دارد.",
            "نوع رویداد",
            "عنوان",
            "شروع",
            "پایان",
            "مکان",
            "یادداشت‌ها",
            "ذخیره تغییرات",
            "انصراف",
            "جلسه",
            'value="آمادگی پیش از بازی"',
            'value="اتاق جلسه ۲"',
        ):
            self.assertContains(response, phrase)

        for phrase in (
            "Termin bearbeiten",
            "Nur die Informationen, die der Trainer später wirklich braucht.",
            "Änderungen speichern",
            "Abbrechen",
        ):
            self.assertNotContains(response, phrase)

    def test_main_persian_pages_use_localized_interface_copy(self):
        expectations = {
            "dashboard": "روزهای آینده",
            "calendar": "تقویم داخلی",
            "players": "فهرست بازیکنان",
            "trainings": "برنامه‌ریزی تمرین",
            "matches": "بازی را ثبت کن؛ عملکرد بازیکنان را بهتر بفهم.",
            "report": "محرمانه · فقط استفاده داخلی",
        }
        for route, phrase in expectations.items():
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, phrase)
