from datetime import date
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from .models import Baho, Fakultet, Fan, Guruh, Menyu, Talaba, Yozuv


class SahifalarTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("admin", password="admin123")
        cls.fakultet = Fakultet.objects.create(nomi="IT")
        cls.guruh = Guruh.objects.create(nomi="101", fakultet=cls.fakultet, yonalish="Dasturlash")
        cls.fan = Fan.objects.create(nomi="Matematika")
        cls.talabalar = [
            Talaba.objects.create(
                familiya=f"Familiya{i}", ism="Ism", jinsi="E", tugilgan_sana=date(2005, 1, 1),
                passport=f"AA000000{i}", guruh=cls.guruh, qabul_yili=2023,
            )
            for i in range(5)
        ]
        cls.baho = Baho.objects.create(talaba=cls.talabalar[0], fan=cls.fan, ball=90, sana=date(2026, 1, 1))

    def setUp(self):
        self.client.login(username="admin", password="admin123")

    def excel_qatorlari(self, response):
        return list(load_workbook(BytesIO(response.content)).active.iter_rows(values_only=True))

    def royxat_idlari(self, nom, **params):
        response = self.client.get(reverse(nom), params)
        self.assertEqual(response.status_code, 200)
        return [o.pk for o in response.context["object_list"]]

    def test_barcha_sahifalar_ochiladi(self):
        sahifalar = [
            ("bosh_sahifa", []), ("talaba_list", []), ("talaba_create", []),
            ("talaba_detail", [self.talabalar[0].pk]),
            ("guruh_list", []), ("guruh_create", []), ("guruh_update", [self.guruh.pk]), ("guruh_delete", [self.guruh.pk]),
            ("fakultet_list", []), ("fakultet_create", []),
            ("fakultet_update", [self.fakultet.pk]), ("fakultet_delete", [self.fakultet.pk]),
            ("fan_list", []), ("fan_create", []), ("fan_update", [self.fan.pk]), ("fan_delete", [self.fan.pk]),
            ("baho_list", []), ("baho_create", []), ("baho_update", [self.baho.pk]), ("baho_delete", [self.baho.pk]),
        ]
        for nom, args in sahifalar:
            with self.subTest(nom):
                self.assertEqual(self.client.get(reverse(nom, args=args)).status_code, 200)

    def test_ochiq_sahifalar_loginsiz_ochiladi_va_shaxsiy_malumot_yoq(self):
        Talaba.objects.filter(pk=self.talabalar[0].pk).update(telefon="+998901234567")
        Fakultet.objects.filter(pk=self.fakultet.pk).update(dekan="Dekanov", telefon="+998712222222")
        Fan.objects.filter(pk=self.fan.pk).update(oqituvchi="Ustozov")
        self.client.logout()
        sahifalar = [
            ("ochiq_sahifa", []), ("ochiq_natijalar", []), ("ochiq_fakultetlar", []),
            ("ochiq_fakultet", [self.fakultet.pk]), ("ochiq_fanlar", []), ("ochiq_fan", [self.fan.pk]), ("ochiq_gpa", []),
        ]
        for nom, args in sahifalar:
            with self.subTest(nom):
                response = self.client.get(reverse(nom, args=args))
                self.assertEqual(response.status_code, 200)
                for maxfiy in ["Familiya0", "AA0000000", "+998901234567", "Dekanov", "+998712222222", "Ustozov"]:
                    self.assertNotContains(response, maxfiy)
        self.assertContains(self.client.get(reverse("ochiq_sahifa")), 'id="slayder"')

    def test_ochiq_sahifalar_kichik_toplam_natijasini_yashiradi(self):
        # Hozircha bitta talabaning bitta bahosi (90) bor
        sahifalar = [
            reverse("ochiq_natijalar"), reverse("ochiq_fakultetlar"), reverse("ochiq_fakultet", args=[self.fakultet.pk]),
            reverse("ochiq_fanlar"), reverse("ochiq_fanlar") + "?tartib=ball", reverse("ochiq_fan", args=[self.fan.pk]),
        ]
        for url in sahifalar:
            with self.subTest(url):
                self.assertNotRegex(self.client.get(url).content.decode(), r"90[.,]0")
        for t in self.talabalar[1:]:
            Baho.objects.create(talaba=t, fan=self.fan, ball=80, sana=date(2026, 1, 1))
        for url in sahifalar:
            with self.subTest(url):
                self.assertRegex(self.client.get(url).content.decode(), r"82[.,]0")

    def test_natijalar_filtri(self):
        boshqa = Guruh.objects.create(nomi="201", fakultet=self.fakultet, yonalish="Tarmoq", kurs=2)
        response = self.client.get(reverse("ochiq_natijalar"), {"kurs": 2})
        self.assertEqual([g.pk for g in response.context["guruhlar"]], [boshqa.pk])
        for qiymat in ["abc", "\u00b2", "9" * 30, "-1"]:
            with self.subTest(qiymat):
                response = self.client.get(reverse("ochiq_natijalar"), {"fakultet": qiymat, "kurs": qiymat, "semestr": qiymat})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["filtr"]["kurs"], "")

    def test_fanlar_qidiruv_va_tartib(self):
        fizika = Fan.objects.create(nomi="Fizika", semestr=2, kredit=9)
        url = reverse("ochiq_fanlar")
        self.assertEqual(list(self.client.get(url, {"q": "fizi"}).context["fanlar"]), [fizika])
        self.assertEqual(list(self.client.get(url, {"semestr": 2}).context["fanlar"]), [fizika])
        self.assertEqual(self.client.get(url, {"tartib": "-kredit"}).context["tartib"], "nomi")
        self.assertEqual(list(self.client.get(url, {"tartib": "kredit"}).context["fanlar"])[-1], fizika)

    def test_ochiq_batafsil_topilmasa_404(self):
        self.assertEqual(self.client.get(reverse("ochiq_fan", args=[999])).status_code, 404)
        self.assertEqual(self.client.get(reverse("ochiq_fakultet", args=[999])).status_code, 404)

    def test_gpa_hisoblash(self):
        fizika = Fan.objects.create(nomi="Fizika", kredit=2)  # Matematika: 4 kredit
        response = self.client.get(reverse("ochiq_gpa"), {f"ball_{self.fan.pk}": "90", f"ball_{fizika.pk}": "60"})
        self.assertAlmostEqual(response.context["gpa"], (5 * 4 + 3 * 2) / 6)
        self.assertEqual(response.context["ortacha"], 75)
        self.assertEqual(response.context["kredit"], 6)
        self.assertContains(response, "talabalar/gpa_formula.svg")

    def test_gpa_notogri_ball_va_saqlanmaslik(self):
        baho_soni = Baho.objects.count()
        for qiymat in ["101", "abc", "-5", "1e2"]:
            with self.subTest(qiymat):
                response = self.client.get(reverse("ochiq_gpa"), {f"ball_{self.fan.pk}": qiymat})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["xato"])
                self.assertIsNone(response.context["gpa"])
        self.assertIsNone(self.client.get(reverse("ochiq_gpa")).context["gpa"])
        self.assertEqual(Baho.objects.count(), baho_soni)

    def test_ichki_sahifalar_login_talab_qiladi(self):
        self.client.logout()
        for nom in ["bosh_sahifa", "talaba_list", "baho_list", "gpa_reyting", "hisobotlar", "talaba_eksport"]:
            with self.subTest(nom):
                self.assertEqual(self.client.get(reverse(nom)).status_code, 302)

    def test_kirish_va_chiqish_yonalishi(self):
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "admin", "password": "admin123"})
        self.assertRedirects(response, reverse("bosh_sahifa"))
        self.assertRedirects(self.client.post(reverse("logout")), reverse("ochiq_sahifa"))

    def test_admin_panel_yonaltiradi(self):
        self.assertRedirects(self.client.get(reverse("admin_panel")), reverse("admin:index"))

    def test_fakultet_qoshish(self):
        response = self.client.post(reverse("fakultet_create"), {"nomi": "Fizika"})
        self.assertRedirects(response, reverse("fakultet_list"))
        self.assertTrue(Fakultet.objects.filter(nomi="Fizika").exists())

    def test_menyu_qoshilib_panelda_korinadi(self):
        response = self.client.post(
            reverse("menyu_create"),
            {"nomi": "Hisobot", "havola": "/fanlar/", "ikonka": "bi-star", "tartib": 1},
        )
        self.assertRedirects(response, reverse("menyu_list"))
        self.assertContains(self.client.get(reverse("talaba_list")), "Hisobot")

    def test_menyu_xavfli_havolani_qabul_qilmaydi(self):
        self.client.post(
            reverse("menyu_create"),
            {"nomi": "Xato", "havola": "javascript:alert(1)", "ikonka": "bi-star", "tartib": 1},
        )
        self.assertFalse(Menyu.objects.exists())

    def test_menyu_sahifalari_ochiladi(self):
        menyu = Menyu.objects.create(nomi="Test", havola="/fanlar/")
        for url in [reverse("menyu_list"), reverse("menyu_update", args=[menyu.pk]), reverse("menyu_delete", args=[menyu.pk])]:
            with self.subTest(url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_panel_menyu_ichki_sahifasiga_olib_boradi(self):
        menyu = Menyu.objects.create(nomi="Test", havola="https://example.com")
        url = reverse("yozuv_list", args=[menyu.pk])
        self.assertContains(self.client.get(reverse("talaba_list")), f'href="{url}"')

    def test_menyuga_yozuv_qoshish_tahrirlash_ochirish(self):
        self.client.post(reverse("menyu_create"), {"nomi": "Kitoblar", "ikonka": "bi-book", "tartib": 1})
        menyu = Menyu.objects.get(nomi="Kitoblar")
        royxat = reverse("yozuv_list", args=[menyu.pk])

        self.assertEqual(self.client.get(reverse("yozuv_create", args=[menyu.pk])).status_code, 200)
        response = self.client.post(reverse("yozuv_create", args=[menyu.pk]), {"sarlavha": "Algebra", "matn": "1-nashr"})
        self.assertRedirects(response, royxat)
        self.assertContains(self.client.get(royxat), "Algebra")
        yozuv = Yozuv.objects.get(menyu=menyu)

        response = self.client.post(reverse("yozuv_update", args=[menyu.pk, yozuv.pk]), {"sarlavha": "Fizika"})
        self.assertRedirects(response, royxat)
        yozuv.refresh_from_db()
        self.assertEqual(yozuv.sarlavha, "Fizika")

        self.assertEqual(self.client.get(reverse("yozuv_delete", args=[menyu.pk, yozuv.pk])).status_code, 200)
        response = self.client.post(reverse("yozuv_delete", args=[menyu.pk, yozuv.pk]))
        self.assertRedirects(response, royxat)
        self.assertFalse(Yozuv.objects.exists())

    def test_yozuvlar_menyular_orasida_aralashmaydi(self):
        a, b = Menyu.objects.create(nomi="A"), Menyu.objects.create(nomi="B")
        yozuv = Yozuv.objects.create(menyu=a, sarlavha="Faqat A")
        self.assertNotContains(self.client.get(reverse("yozuv_list", args=[b.pk])), "Faqat A")
        self.assertEqual(self.client.get(reverse("yozuv_update", args=[b.pk, yozuv.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("yozuv_create", args=[999])).status_code, 404)

    def test_ichida_yozuvi_bor_menyu_ochirilmaydi(self):
        menyu = Menyu.objects.create(nomi="A")
        Yozuv.objects.create(menyu=menyu, sarlavha="X")
        self.client.post(reverse("menyu_delete", args=[menyu.pk]))
        self.assertTrue(Menyu.objects.filter(pk=menyu.pk).exists())

    def test_gpa_kredit_bilan_hisoblanadi(self):
        talaba = self.talabalar[0]  # Matematika: 4 kredit, baho 5
        fan = Fan.objects.create(nomi="Fizika", kredit=2)
        Baho.objects.create(talaba=talaba, fan=fan, ball=60, sana=date(2026, 1, 1))  # baho 3
        self.assertAlmostEqual(talaba.gpa, (5 * 4 + 3 * 2) / 6)
        self.assertIsNone(self.talabalar[1].gpa)

    def test_kredit_nol_bolsa_gpa_xato_bermaydi(self):
        fan = Fan.objects.create(nomi="Sport", kredit=0)
        Baho.objects.create(talaba=self.talabalar[1], fan=fan, ball=90, sana=date(2026, 1, 1))
        self.assertIsNone(self.talabalar[1].gpa)

    def test_gpa_reyting_tartibi_va_filtri(self):
        Baho.objects.create(talaba=self.talabalar[1], fan=self.fan, ball=60, sana=date(2026, 1, 1))
        ro = self.client.get(reverse("gpa_reyting"))
        self.assertEqual(list(ro.context["object_list"]), [self.talabalar[0], self.talabalar[1]])
        self.assertEqual(self.client.get("/gpa").status_code, 301)
        self.assertEqual(self.client.get(reverse("gpa_reyting"), {"guruh": "abc"}).status_code, 200)
        self.assertEqual(len(self.client.get(reverse("gpa_reyting"), {"guruh": 999}).context["object_list"]), 0)

    def test_hisobotlar(self):
        past = Baho.objects.create(talaba=self.talabalar[1], fan=self.fan, ball=40, sana=date(2026, 1, 1))
        response = self.client.get(reverse("hisobotlar"))
        self.assertEqual(list(response.context["ozlashtirmaganlar"]), [past])
        self.assertEqual(response.context["guruhlar"][0].ortacha, 65)
        self.assertEqual(response.context["fakultetlar"][0].soni, 5)

    def test_talaba_eksport_filtr_bilan(self):
        response = self.client.get(reverse("talaba_eksport"), {"id": self.talabalar[0].pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn(".xlsx", response["Content-Disposition"])
        qatorlar = self.excel_qatorlari(response)
        self.assertEqual(qatorlar[0][:3], ("ID", "Familiya", "Ism"))
        self.assertEqual(len(qatorlar), 2)
        self.assertEqual(qatorlar[1][0], self.talabalar[0].pk)
        self.assertEqual(qatorlar[1][1], "Familiya0")
        self.assertEqual(qatorlar[1][-1], 5)

    def test_baho_eksport(self):
        qatorlar = self.excel_qatorlari(self.client.get(reverse("baho_eksport")))
        self.assertEqual(qatorlar[1][2], "Matematika")

    def test_eksport_formulani_matn_qiladi(self):
        Talaba.objects.filter(pk=self.talabalar[0].pk).update(familiya="=1+1", telefon="+998901234567")
        response = self.client.get(reverse("talaba_eksport"), {"id": self.talabalar[0].pk})
        katak = load_workbook(BytesIO(response.content)).active["B2"]
        self.assertEqual(katak.value, "=1+1")
        self.assertEqual(katak.data_type, "s")
        self.assertEqual(self.excel_qatorlari(response)[1][8], "+998901234567")

    def test_admin_holat_amali(self):
        talaba = self.talabalar[0]
        self.client.post(
            reverse("admin:talabalar_talaba_changelist"),
            {"action": "holat_bitirgan", "_selected_action": [talaba.pk]},
        )
        talaba.refresh_from_db()
        self.assertEqual(talaba.holati, "bitirgan")

    def test_admin_menyu_va_yozuv(self):
        for nom in ["admin:talabalar_menyu_changelist", "admin:talabalar_yozuv_changelist"]:
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200)

    def test_standart_tartib_familiya_boyicha(self):
        familiyalar = [o.familiya for o in self.client.get(reverse("talaba_list")).context["object_list"]]
        self.assertEqual(familiyalar, sorted(familiyalar))

    def test_id_boyicha_saralash(self):
        idlar = sorted(t.pk for t in self.talabalar)
        self.assertEqual(self.royxat_idlari("talaba_list", tartib="id"), idlar)
        self.assertEqual(self.royxat_idlari("talaba_list", tartib="-id"), idlar[::-1])

    def test_id_boyicha_filtr(self):
        a, b, c, d, e = sorted(t.pk for t in self.talabalar)
        self.assertEqual(self.royxat_idlari("talaba_list", id=str(c)), [c])
        self.assertEqual(self.royxat_idlari("talaba_list", id=f"{a}, {e}", tartib="id"), [a, e])
        self.assertEqual(self.royxat_idlari("talaba_list", id=f"{b}-{d}", tartib="id"), [b, c, d])
        self.assertEqual(self.royxat_idlari("talaba_list", id=f"{d}-{b}", tartib="id"), [b, c, d])

    def test_notogri_id_xato_bermaydi(self):
        for matn in ["abc", "1-", "1;2", ",", "9" * 30]:
            with self.subTest(matn):
                self.assertEqual(self.royxat_idlari("talaba_list", id=matn), [])

    def test_boshqa_royxatlarda_id_filtr(self):
        self.assertEqual(self.royxat_idlari("guruh_list", id=self.guruh.pk), [self.guruh.pk])
        self.assertEqual(self.royxat_idlari("fakultet_list", id=self.fakultet.pk), [self.fakultet.pk])
        self.assertEqual(self.royxat_idlari("fan_list", id=self.fan.pk), [self.fan.pk])
        self.assertEqual(self.royxat_idlari("baho_list", id=self.baho.pk), [self.baho.pk])

    def test_notogri_tartib_etiborsiz_qoldiriladi(self):
        self.assertEqual(len(self.royxat_idlari("talaba_list", tartib="parol")), 5)
