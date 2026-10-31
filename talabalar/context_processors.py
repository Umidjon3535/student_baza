from django.conf import settings

from .models import Menyu


def menyular(request):
    return {"menyular": Menyu.objects.all(), "vaqtinchalik_baza": settings.VERCEL}
