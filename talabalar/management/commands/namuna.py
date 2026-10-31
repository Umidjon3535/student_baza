import random
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from talabalar.models import Baho, Fakultet, Fan, Guruh, Talaba

FAMILIYALAR = ["Karimov", "Toshmatov", "Aliyev", "Rahimov", "Yusupov", "Qodirov", "Ergashev", "Nazarov", "Saidov", "Xolmatov"]
ERKAK_ISMLAR = ["Aziz", "Sardor", "Jasur", "Bekzod", "Otabek", "Sherzod", "Dilshod", "Javohir"]
AYOL_ISMLAR = ["Madina", "Dilnoza", "Gulnora", "Malika", "Nilufar", "Sevara", "Zarina", "Shahzoda"]
OTA_ISMLAR = ["Anvar", "Bahodir", "Rustam", "Shavkat", "Ulug'bek", "Hamid"]


class Command(BaseCommand):
    help = "Bazani namunaviy ma'lumotlar bilan to'ldiradi va admin/admin123 foydalanuvchisini yaratadi"

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "", "admin123")

        if Talaba.objects.exists():
            self.stdout.write("Bazada allaqachon ma'lumotlar bor.")
            return

        it = Fakultet.objects.create(nomi="Axborot texnologiyalari", dekan="Abdullayev R.", telefon="+998712000001")
        iqt = Fakultet.objects.create(nomi="Iqtisodiyot", dekan="Mirzayev S.", telefon="+998712000002")

        guruhlar = [
            Guruh.objects.create(nomi="AT-21", fakultet=it, yonalish="Kompyuter injiniringi", kurs=3),
            Guruh.objects.create(nomi="DI-22", fakultet=it, yonalish="Dasturiy injiniring", kurs=2),
            Guruh.objects.create(nomi="IQ-23", fakultet=iqt, yonalish="Iqtisodiyot", kurs=1),
        ]
        fanlar = [
            Fan.objects.create(nomi="Ma'lumotlar bazasi", kredit=6, semestr=3, oqituvchi="Nurmatov A."),
            Fan.objects.create(nomi="Dasturlash asoslari", kredit=6, semestr=1, oqituvchi="Islomov B."),
            Fan.objects.create(nomi="Oliy matematika", kredit=5, semestr=1, oqituvchi="Hasanov D."),
            Fan.objects.create(nomi="Ingliz tili", kredit=4, semestr=2, oqituvchi="Sobirova M."),
        ]

        random.seed(1)
        for i in range(30):
            jins = random.choice("EA")
            familiya = random.choice(FAMILIYALAR)
            if jins == "A":
                familiya += "a"
            ota = random.choice(OTA_ISMLAR)
            talaba = Talaba.objects.create(
                familiya=familiya,
                ism=random.choice(ERKAK_ISMLAR if jins == "E" else AYOL_ISMLAR),
                otasining_ismi=ota + (" o'g'li" if jins == "E" else " qizi"),
                jinsi=jins,
                tugilgan_sana=date(2003, 1, 1) + timedelta(days=random.randint(0, 1500)),
                passport=f"AB{1000000 + i:07d}",
                telefon=f"+99890{random.randint(1000000, 9999999)}",
                manzil="Toshkent sh.",
                guruh=random.choice(guruhlar),
                qabul_yili=random.choice([2021, 2022, 2023]),
                talim_shakli=random.choice(["grant", "kontrakt", "kontrakt"]),
            )
            for fan in random.sample(fanlar, 3):
                Baho.objects.create(talaba=talaba, fan=fan, ball=random.randint(45, 100), sana=date(2026, 1, 15))

        self.stdout.write(self.style.SUCCESS("Namunaviy ma'lumotlar qo'shildi. Login: admin / Parol: admin123"))
