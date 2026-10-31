from .models import Menyu


def menyular(request):
    return {"menyular": Menyu.objects.all()}
