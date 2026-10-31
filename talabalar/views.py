import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Avg, Count, F, ProtectedError, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .forms import BahoForm, FakultetForm, FanForm, GuruhForm, MenyuForm, TalabaForm, YozuvForm
from .models import Baho, Fakultet, Fan, Guruh, Menyu, Talaba, Yozuv


ID_QISMI = re.compile(r"(\d{1,18})(?:\s*-\s*(\d{1,18}))?")



def id_sharti(matn):
    """'3', '1,5,7' yoki '10-20' ko'rinishidagi matnni Q ga aylantiradi; xato bo'lsa None."""
    shart = Q()
    for qism in filter(None, (q.strip() for q in matn.split(","))):
        topilgan = ID_QISMI.fullmatch(qism)
        if not topilgan:
            return None
        boshi, oxiri = topilgan.groups()
        if oxiri:
            shart |= Q(pk__range=sorted((int(boshi), int(oxiri))))
        else:
            shart |= Q(pk=int(boshi))
    return shart or None


class BoshSahifa(LoginRequiredMixin, TemplateView):
    template_name = "talabalar/bosh_sahifa.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            talaba_soni=Talaba.objects.count(),
            guruh_soni=Guruh.objects.count(),
            fakultet_soni=Fakultet.objects.count(),
            fan_soni=Fan.objects.count(),
            grant_soni=Talaba.objects.filter(talim_shakli="grant").count(),
            kontrakt_soni=Talaba.objects.filter(talim_shakli="kontrakt").count(),
            fakultetlar=Fakultet.objects.annotate(soni=Count("guruhlar__talabalar")),
            eng_yaxshilar=Talaba.objects.annotate(ortacha=Avg("baholar__ball"))
            .filter(ortacha__isnull=False)
            .select_related("guruh")
            .order_by("-ortacha")[:5],
            oxirgilar=Talaba.objects.select_related("guruh").order_by("-yaratilgan")[:5],
        )
        return ctx
class ObyektMixin(LoginRequiredMixin):
    sarlavha = ""
    list_url = ""

    def get_orqaga_url(self):
        return reverse(self.list_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sarlavha"] = self.sarlavha
        ctx["orqaga_url"] = self.get_orqaga_url()
        return ctx


class ObyektCreate(ObyektMixin, SuccessMessageMixin, CreateView):
    template_name = "talabalar/obyekt_form.html"
    success_message = "Muvaffaqiyatli qo'shildi"


class ObyektUpdate(ObyektMixin, SuccessMessageMixin, UpdateView):
    template_name = "talabalar/obyekt_form.html"
    success_message = "O'zgarishlar saqlandi"


class ObyektDelete(ObyektMixin, DeleteView):
    template_name = "talabalar/obyekt_confirm_delete.html"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "O'chirib bo'lmaydi: bu yozuvga boshqa ma'lumotlar bog'langan.")
            return redirect(self.success_url)
        messages.success(self.request, "O'chirildi")
        return response

class IdRoyxatMixin(LoginRequiredMixin):
    """Ro'yxatga ?id=1,5,10-20 filtri va ?tartib=id / ?tartib=-id saralashini qo'shadi."""

    def get_queryset(self):
        qs = super().get_queryset()
        g = self.request.GET
        if matn := g.get("id", "").strip():
            shart = id_sharti(matn)
            if shart is None:
                messages.error(self.request, "ID noto'g'ri kiritildi. Namuna: 3 yoki 1,5,7 yoki 10-20")
                return qs.none()
            qs = qs.filter(shart)
        if g.get("tartib") in ("id", "-id"):
            qs = qs.order_by(g["tartib"])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        querystring = params.urlencode()
        params.pop("tartib", None)
        ctx.update(
            filtr=self.request.GET,
            querystring=querystring,
            tartibsiz_querystring=params.urlencode(),
            keyingi_tartib="-id" if self.request.GET.get("tartib") == "id" else "id",
        )
        return ctx


class TalabaList(IdRoyxatMixin, ListView):
    model = Talaba
    ordering = ["familiya", "ism"]
    paginate_by = 15
    template_name = "talabalar/talaba_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("guruh__fakultet").annotate(ortacha=Avg("baholar__ball"))
        g = self.request.GET
        if q := g.get("q", "").strip():
            qs = qs.filter(
                Q(familiya__icontains=q) | Q(ism__icontains=q) | Q(otasining_ismi__icontains=q)
                | Q(passport__icontains=q) | Q(telefon__icontains=q)
            )
        if g.get("fakultet"):
            qs = qs.filter(guruh__fakultet_id=g["fakultet"])
        if g.get("guruh"):
            qs = qs.filter(guruh_id=g["guruh"])
        if g.get("talim_shakli"):
            qs = qs.filter(talim_shakli=g["talim_shakli"])
        if g.get("holati"):
            qs = qs.filter(holati=g["holati"])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            fakultetlar=Fakultet.objects.all(),
            guruhlar=Guruh.objects.all(),
            talim_shakllari=Talaba.TALIM_SHAKLI,
            holatlar=Talaba.HOLAT,
        )
        return ctx


class TalabaDetail(LoginRequiredMixin, DetailView):
    queryset = Talaba.objects.prefetch_related("baholar__fan")
    template_name = "talabalar/talaba_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["baholar"] = self.object.baholar.select_related("fan")
        ctx["ortacha"] = self.object.ortacha_ball()
        return ctx


class TalabaCreate(ObyektCreate):
    model, form_class = Talaba, TalabaForm
    sarlavha, list_url = "Yangi talaba", "talaba_list"


class TalabaUpdate(ObyektUpdate):
    model, form_class = Talaba, TalabaForm
    sarlavha, list_url = "Talabani tahrirlash", "talaba_list"


class TalabaDelete(ObyektDelete):
    model = Talaba
    sarlavha, list_url = "Talabani o'chirish", "talaba_list"
    success_url = reverse_lazy("talaba_list")


# --- Guruhlar ---

class GuruhList(IdRoyxatMixin, ListView):
    template_name = "talabalar/guruh_list.html"
    queryset = Guruh.objects.select_related("fakultet").annotate(soni=Count("talabalar"))

class GuruhCreate(ObyektCreate):
    model, form_class = Guruh, GuruhForm
    sarlavha, list_url = "Yangi guruh", "guruh_list"
    success_url = reverse_lazy("guruh_list")

class GuruhUpdate(ObyektUpdate):
    model, form_class = Guruh, GuruhForm
    sarlavha, list_url = "Guruhni tahrirlash", "guruh_list"
    success_url = reverse_lazy("guruh_list")

class GuruhDelete(ObyektDelete):
    model = Guruh
    sarlavha, list_url = "Guruhni o'chirish", "guruh_list"
    success_url = reverse_lazy("guruh_list")


# --- Fakultetlar ---
class FakultetList(IdRoyxatMixin, ListView):
    template_name = "talabalar/fakultet_list.html"
    queryset = Fakultet.objects.annotate(
        guruh_soni=Count("guruhlar", distinct=True), talaba_soni=Count("guruhlar__talabalar")
    )

class FakultetCreate(ObyektCreate):
    model, form_class = Fakultet, FakultetForm
    sarlavha, list_url = "Yangi fakultet", "fakultet_list"
    success_url = reverse_lazy("fakultet_list")

class FakultetUpdate(ObyektUpdate):
    model, form_class = Fakultet, FakultetForm
    sarlavha, list_url = "Fakultetni tahrirlash", "fakultet_list"
    success_url = reverse_lazy("fakultet_list")

class FakultetDelete(ObyektDelete):
    model = Fakultet
    sarlavha, list_url = "Fakultetni o'chirish", "fakultet_list"
    success_url = reverse_lazy("fakultet_list")


# --- Fanlar ---
class FanList(IdRoyxatMixin, ListView):
    template_name = "talabalar/fan_list.html"
    queryset = Fan.objects.annotate(ortacha=Avg("baholar__ball"), soni=Count("baholar"))

class FanCreate(ObyektCreate):
    model, form_class = Fan, FanForm
    sarlavha, list_url = "Yangi fan", "fan_list"
    success_url = reverse_lazy("fan_list")

class FanUpdate(ObyektUpdate):
    model, form_class = Fan, FanForm
    sarlavha, list_url = "Fanni tahrirlash", "fan_list"
    success_url = reverse_lazy("fan_list")

class FanDelete(ObyektDelete):
    model = Fan
    sarlavha, list_url = "Fanni o'chirish", "fan_list"
    success_url = reverse_lazy("fan_list")

# --- Baholar ---

class BahoList(IdRoyxatMixin, ListView):
    template_name = "talabalar/baho_list.html"
    paginate_by = 20
    queryset = Baho.objects.select_related("talaba", "fan")

    def get_queryset(self):
        qs = super().get_queryset()
        if fan := self.request.GET.get("fan"):
            qs = qs.filter(fan_id=fan)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["fanlar"] = Fan.objects.all()
        ctx["tanlangan_fan"] = self.request.GET.get("fan", "")
        return ctx


class BahoCreate(ObyektCreate):
    model, form_class = Baho, BahoForm
    sarlavha, list_url = "Baho qo'yish", "baho_list"
    success_url = reverse_lazy("baho_list")

    def get_initial(self):
        return {"talaba": self.request.GET.get("talaba")}


class BahoUpdate(ObyektUpdate):
    model, form_class = Baho, BahoForm
    sarlavha, list_url = "Bahoni tahrirlash", "baho_list"
    success_url = reverse_lazy("baho_list")


class BahoDelete(ObyektDelete):
    model = Baho
    sarlavha, list_url = "Bahoni o'chirish", "baho_list"
    success_url = reverse_lazy("baho_list")


# --- Menyular ---

class MenyuList(IdRoyxatMixin, ListView):
    model = Menyu
    template_name = "talabalar/menyu_list.html"


class MenyuCreate(ObyektCreate):
    model, form_class = Menyu, MenyuForm
    sarlavha, list_url = "Yangi menyu", "menyu_list"
    success_url = reverse_lazy("menyu_list")


class MenyuUpdate(ObyektUpdate):
    model, form_class = Menyu, MenyuForm
    sarlavha, list_url = "Menyuni tahrirlash", "menyu_list"
    success_url = reverse_lazy("menyu_list")


class MenyuDelete(ObyektDelete):
    model = Menyu
    sarlavha, list_url = "Menyuni o'chirish", "menyu_list"
    success_url = reverse_lazy("menyu_list")


# --- Menyu ichidagi yozuvlar ---

class YozuvList(IdRoyxatMixin, ListView):
    model = Yozuv
    paginate_by = 20
    template_name = "talabalar/yozuv_list.html"

    def get_queryset(self):
        self.menyu = get_object_or_404(Menyu, pk=self.kwargs["menyu_pk"])
        return super().get_queryset().filter(menyu=self.menyu)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["menyu"] = self.menyu
        return ctx


class YozuvMixin:
    def get_orqaga_url(self):
        return reverse("yozuv_list", args=[self.kwargs["menyu_pk"]])

    def get_success_url(self):
        return self.get_orqaga_url()

    def get_queryset(self):
        return Yozuv.objects.filter(menyu_id=self.kwargs["menyu_pk"])


class YozuvCreate(YozuvMixin, ObyektCreate):
    model, form_class = Yozuv, YozuvForm
    sarlavha = "Yangi yozuv"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = Yozuv(menyu=get_object_or_404(Menyu, pk=self.kwargs["menyu_pk"]))
        return kwargs


class YozuvUpdate(YozuvMixin, ObyektUpdate):
    model, form_class = Yozuv, YozuvForm
    sarlavha = "Yozuvni tahrirlash"


class YozuvDelete(YozuvMixin, ObyektDelete):
    model = Yozuv
    sarlavha = "Yozuvni o'chirish"


# --- GPA va hisobotlar ---

class GpaReyting(LoginRequiredMixin, ListView):
    template_name = "talabalar/gpa_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = Talaba.objects.select_related("guruh").prefetch_related("baholar__fan")
        guruh = self.request.GET.get("guruh", "")
        if guruh.isdigit():
            qs = qs.filter(guruh_id=guruh)
        return sorted((t for t in qs if t.gpa is not None), key=lambda t: t.gpa, reverse=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["guruhlar"] = Guruh.objects.all()
        ctx["tanlangan_guruh"] = self.request.GET.get("guruh", "")
        return ctx


class Hisobotlar(LoginRequiredMixin, TemplateView):
    template_name = "talabalar/hisobotlar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        yuqori = F("ortacha").desc(nulls_last=True)
        ctx.update(
            guruhlar=Guruh.objects.annotate(
                ortacha=Avg("talabalar__baholar__ball"), soni=Count("talabalar", distinct=True)
            ).order_by(yuqori),
            fakultetlar=Fakultet.objects.annotate(
                ortacha=Avg("guruhlar__talabalar__baholar__ball"), soni=Count("guruhlar__talabalar", distinct=True)
            ).order_by(yuqori),
            ozlashtirmaganlar=Baho.objects.filter(ball__lt=55)
            .select_related("talaba__guruh", "fan")
            .order_by("talaba__familiya", "talaba__ism", "fan__nomi"),
        )
        return ctx


# --- Excel eksport ---

def excel_javob(fayl_nomi, sarlavhalar, qatorlar):
    kitob = Workbook()
    varaq = kitob.active
    varaq.append(sarlavhalar)
    for katak in varaq[1]:
        katak.font = Font(bold=True)
    varaq.freeze_panes = "A2"
    for qator in qatorlar:
        varaq.append(qator)
        for katak in varaq[varaq.max_row]:
            # "=" bilan boshlangan matn formula bo'lib bajarilmasligi uchun
            if isinstance(katak.value, str):
                katak.data_type = "s"
    for i, ustun in enumerate(varaq.columns, start=1):
        eni = max(len(str(k.value)) for k in ustun if k.value is not None)
        varaq.column_dimensions[get_column_letter(i)].width = eni + 2

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{fayl_nomi}"'
    kitob.save(response)
    return response


class TalabaEksport(TalabaList):
    def get(self, request, *args, **kwargs):
        qs = self.get_queryset().prefetch_related("baholar__fan")
        return excel_javob(
            "talabalar.xlsx",
            ["ID", "Familiya", "Ism", "Otasining ismi", "Guruh", "Fakultet", "Ta'lim shakli", "Holati", "Telefon", "O'rtacha ball", "GPA"],
            (
                [
                    t.pk, t.familiya, t.ism, t.otasining_ismi, t.guruh.nomi, t.guruh.fakultet.nomi,
                    t.get_talim_shakli_display(), t.get_holati_display(), t.telefon,
                    round(t.ortacha, 1) if t.ortacha is not None else None,
                    round(t.gpa, 2) if t.gpa is not None else None,
                ]
                for t in qs
            ),
        )


class BahoEksport(BahoList):
    def get(self, request, *args, **kwargs):
        return excel_javob(
            "baholar.xlsx",
            ["ID", "Talaba", "Fan", "Ball", "Baho", "Sana"],
            ([b.pk, b.talaba.toliq_ism, b.fan.nomi, b.ball, b.baho, b.sana] for b in self.get_queryset()),
        )
