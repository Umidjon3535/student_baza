"""Hamma uchun ochiq sahifalar: faqat umumiy statistika, shaxsiy ma'lumotlarsiz."""
import re

from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import Baho, Fakultet, Fan, Guruh, Talaba, ball_bahosi

# Bundan kam talaba baholangan to'plamning natijasi ko'rsatilmaydi: alohida talabaning bahosi bilinib qolmasin
ANONIM_CHEGARA = 5


def son_parametr(matn):
    """URL parametri musbat butun son bo'lsa o'zini, aks holda bo'sh qator qaytaradi."""
    return matn if re.fullmatch(r"[0-9]{1,9}", matn or "") else ""


def taqsimot(baholar):
    hisob = baholar.aggregate(
        jami=Count("pk"),
        talaba=Count("talaba", distinct=True),
        ortacha=Avg("ball"),
        a5=Count("pk", filter=Q(ball__gte=86)),
        a4=Count("pk", filter=Q(ball__gte=71, ball__lt=86)),
        a3=Count("pk", filter=Q(ball__gte=55, ball__lt=71)),
        a2=Count("pk", filter=Q(ball__lt=55)),
    )
    if hisob["talaba"] < ANONIM_CHEGARA:
        return {"korsatish": False, "jami": hisob["jami"], "chegara": ANONIM_CHEGARA}
    jami = hisob["jami"]
    return {
        "korsatish": True,
        "jami": jami,
        "talaba": hisob["talaba"],
        "ortacha": hisob["ortacha"],
        "otish_foizi": round((jami - hisob["a2"]) * 100 / jami),
        "qatorlar": [
            {"baho": b, "soni": hisob[f"a{b}"], "foiz": round(hisob[f"a{b}"] * 100 / jami)}
            for b in (5, 4, 3, 2)
        ],
    }


def ortachani_ochish(obyektlar):
    """Faqat chegaradan o'tganlarga ochiq_ortacha beradi; shablon boshqa o'rtachani ishlatmaydi."""
    natija = list(obyektlar)
    for o in natija:
        o.ochiq_ortacha = o.ortacha if o.baholangan >= ANONIM_CHEGARA else None
    return natija


def yuqori_ball_boyicha(obyektlar):
    return sorted(obyektlar, key=lambda o: (o.ochiq_ortacha is None, -(o.ochiq_ortacha or 0)))


class OchiqKontekst(TemplateView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["chegara"] = ANONIM_CHEGARA
        return ctx


class OchiqSahifa(OchiqKontekst):
    template_name = "talabalar/ochiq_sahifa.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            talaba_soni=Talaba.objects.count(),
            guruh_soni=Guruh.objects.count(),
            fakultet_soni=Fakultet.objects.count(),
            fan_soni=Fan.objects.count(),
            baho_soni=Baho.objects.count(),
        )
        return ctx


class Natijalar(OchiqKontekst):
    template_name = "talabalar/ochiq_natijalar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        filtr = {k: son_parametr(g.get(k)) for k in ("fakultet", "kurs", "semestr")}

        baholar = Baho.objects.all()
        guruhlar = Guruh.objects.select_related("fakultet")
        shart = Q(talabalar__baholar__isnull=False)
        if filtr["fakultet"]:
            baholar = baholar.filter(talaba__guruh__fakultet_id=filtr["fakultet"])
            guruhlar = guruhlar.filter(fakultet_id=filtr["fakultet"])
        if filtr["kurs"]:
            baholar = baholar.filter(talaba__guruh__kurs=filtr["kurs"])
            guruhlar = guruhlar.filter(kurs=filtr["kurs"])
        if filtr["semestr"]:
            baholar = baholar.filter(fan__semestr=filtr["semestr"])
            shart &= Q(talabalar__baholar__fan__semestr=filtr["semestr"])
        guruhlar = guruhlar.annotate(
            ortacha=Avg("talabalar__baholar__ball", filter=shart),
            baholangan=Count("talabalar", filter=shart, distinct=True),
        )
        ctx.update(
            filtr=filtr,
            taqsimot=taqsimot(baholar),
            guruhlar=yuqori_ball_boyicha(ortachani_ochish(guruhlar)),
            fakultetlar=Fakultet.objects.all(),
            kurslar=Guruh.objects.order_by("kurs").values_list("kurs", flat=True).distinct(),
            semestrlar=Fan.objects.order_by("semestr").values_list("semestr", flat=True).distinct(),
        )
        return ctx


class Fakultetlar(OchiqKontekst):
    template_name = "talabalar/ochiq_fakultetlar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        fakultetlar = Fakultet.objects.annotate(
            guruh_soni=Count("guruhlar", distinct=True),
            soni=Count("guruhlar__talabalar", distinct=True),
            baholangan=Count(
                "guruhlar__talabalar", filter=Q(guruhlar__talabalar__baholar__isnull=False), distinct=True
            ),
            ortacha=Avg("guruhlar__talabalar__baholar__ball"),
        )
        if q:
            fakultetlar = fakultetlar.filter(nomi__icontains=q)
        ctx.update(q=q, fakultetlar=ortachani_ochish(fakultetlar))
        return ctx


class FakultetBatafsil(OchiqKontekst):
    template_name = "talabalar/ochiq_fakultet.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fakultet = get_object_or_404(Fakultet, pk=self.kwargs["pk"])
        guruhlar = fakultet.guruhlar.annotate(
            soni=Count("talabalar", distinct=True),
            baholangan=Count("talabalar", filter=Q(talabalar__baholar__isnull=False), distinct=True),
            ortacha=Avg("talabalar__baholar__ball"),
        )
        ctx.update(
            fakultet=fakultet,
            guruhlar=ortachani_ochish(guruhlar),
            taqsimot=taqsimot(Baho.objects.filter(talaba__guruh__fakultet=fakultet)),
        )
        return ctx


class Fanlar(OchiqKontekst):
    template_name = "talabalar/ochiq_fanlar.html"
    TARTIBLAR = {"nomi": "Nomi", "semestr": "Semestr", "kredit": "Kredit", "ball": "O'rtacha ball"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        q = g.get("q", "").strip()
        semestr = son_parametr(g.get("semestr"))
        tartib = g.get("tartib") if g.get("tartib") in self.TARTIBLAR else "nomi"

        fanlar = Fan.objects.annotate(ortacha=Avg("baholar__ball"), baholangan=Count("baholar"))
        if q:
            fanlar = fanlar.filter(nomi__icontains=q)
        if semestr:
            fanlar = fanlar.filter(semestr=semestr)
        if tartib == "ball":
            # Yashirilgan o'rtacha tartib orqali ham bilinmasligi uchun ochiq qiymat bo'yicha saralanadi
            fanlar = yuqori_ball_boyicha(ortachani_ochish(fanlar))
        else:
            fanlar = ortachani_ochish(fanlar.order_by(tartib, "nomi"))
        ctx.update(
            q=q,
            semestr=semestr,
            tartib=tartib,
            tartiblar=self.TARTIBLAR.items(),
            fanlar=fanlar,
            semestrlar=Fan.objects.order_by("semestr").values_list("semestr", flat=True).distinct(),
        )
        return ctx


class FanBatafsil(OchiqKontekst):
    template_name = "talabalar/ochiq_fan.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fan = get_object_or_404(Fan, pk=self.kwargs["pk"])
        shart = Q(guruhlar__talabalar__baholar__fan=fan)
        fakultetlar = Fakultet.objects.annotate(
            ortacha=Avg("guruhlar__talabalar__baholar__ball", filter=shart),
            baholangan=Count("guruhlar__talabalar", filter=shart, distinct=True),
        ).filter(baholangan__gt=0)
        ctx.update(
            fan=fan,
            taqsimot=taqsimot(fan.baholar.all()),
            fakultetlar=yuqori_ball_boyicha(ortachani_ochish(fakultetlar)),
        )
        return ctx


class GpaHisoblash(OchiqKontekst):
    """Foydalanuvchi kiritgan ballardan GPA hisoblaydi; hech narsa saqlanmaydi."""

    template_name = "talabalar/ochiq_gpa.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fanlar = list(Fan.objects.all())
        kiritilganlar = []
        xato = False
        for fan in fanlar:
            fan.kiritilgan = self.request.GET.get(f"ball_{fan.pk}", "").strip()
            fan.baho = None
            if not fan.kiritilgan:
                continue
            if re.fullmatch(r"[0-9]{1,3}", fan.kiritilgan) and int(fan.kiritilgan) <= 100:
                fan.baho = ball_bahosi(int(fan.kiritilgan))
                kiritilganlar.append(fan)
            else:
                fan.xato = xato = True

        kredit = sum(f.kredit for f in kiritilganlar)
        ctx.update(
            fanlar=fanlar,
            xato=xato,
            kiritildi=bool(kiritilganlar),
            kredit=kredit,
            gpa=sum(f.baho * f.kredit for f in kiritilganlar) / kredit if kredit else None,
            ortacha=sum(int(f.kiritilgan) for f in kiritilganlar) / len(kiritilganlar) if kiritilganlar else None,
        )
        return ctx
