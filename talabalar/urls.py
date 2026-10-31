from django.urls import path
from django.views.generic import RedirectView

from . import ochiq, views

urlpatterns = [
    path("", ochiq.OchiqSahifa.as_view(), name="ochiq_sahifa"),
    path("sayt/natijalar/", ochiq.Natijalar.as_view(), name="ochiq_natijalar"),
    path("sayt/fakultetlar/", ochiq.Fakultetlar.as_view(), name="ochiq_fakultetlar"),
    path("sayt/fakultetlar/<int:pk>/", ochiq.FakultetBatafsil.as_view(), name="ochiq_fakultet"),
    path("sayt/fanlar/", ochiq.Fanlar.as_view(), name="ochiq_fanlar"),
    path("sayt/fanlar/<int:pk>/", ochiq.FanBatafsil.as_view(), name="ochiq_fan"),
    path("sayt/gpa/", ochiq.GpaHisoblash.as_view(), name="ochiq_gpa"),

    path("boshqaruv/", views.BoshSahifa.as_view(), name="bosh_sahifa"),
    path("admin-panel/", RedirectView.as_view(pattern_name="admin:index"), name="admin_panel"),
    path("gpa/", views.GpaReyting.as_view(), name="gpa_reyting"),
    path("hisobotlar/", views.Hisobotlar.as_view(), name="hisobotlar"),
    path("talabalar/eksport/", views.TalabaEksport.as_view(), name="talaba_eksport"),
    path("baholar/eksport/", views.BahoEksport.as_view(), name="baho_eksport"),

    path("talabalar/", views.TalabaList.as_view(), name="talaba_list"),
    path("talabalar/yangi/", views.TalabaCreate.as_view(), name="talaba_create"),
    path("talabalar/<int:pk>/", views.TalabaDetail.as_view(), name="talaba_detail"),
    path("talabalar/<int:pk>/tahrirlash/", views.TalabaUpdate.as_view(), name="talaba_update"),
    path("talabalar/<int:pk>/ochirish/", views.TalabaDelete.as_view(), name="talaba_delete"),

    path("guruhlar/", views.GuruhList.as_view(), name="guruh_list"),
    path("guruhlar/yangi/", views.GuruhCreate.as_view(), name="guruh_create"),
    path("guruhlar/<int:pk>/tahrirlash/", views.GuruhUpdate.as_view(), name="guruh_update"),
    path("guruhlar/<int:pk>/ochirish/", views.GuruhDelete.as_view(), name="guruh_delete"),

    path("fakultetlar/", views.FakultetList.as_view(), name="fakultet_list"),
    path("fakultetlar/yangi/", views.FakultetCreate.as_view(), name="fakultet_create"),
    path("fakultetlar/<int:pk>/tahrirlash/", views.FakultetUpdate.as_view(), name="fakultet_update"),
    path("fakultetlar/<int:pk>/ochirish/", views.FakultetDelete.as_view(), name="fakultet_delete"),

    path("fanlar/", views.FanList.as_view(), name="fan_list"),
    path("fanlar/yangi/", views.FanCreate.as_view(), name="fan_create"),
    path("fanlar/<int:pk>/tahrirlash/", views.FanUpdate.as_view(), name="fan_update"),
    path("fanlar/<int:pk>/ochirish/", views.FanDelete.as_view(), name="fan_delete"),

    path("baholar/", views.BahoList.as_view(), name="baho_list"),
    path("baholar/yangi/", views.BahoCreate.as_view(), name="baho_create"),
    path("baholar/<int:pk>/tahrirlash/", views.BahoUpdate.as_view(), name="baho_update"),
    path("baholar/<int:pk>/ochirish/", views.BahoDelete.as_view(), name="baho_delete"),

    path("menyular/", views.MenyuList.as_view(), name="menyu_list"),
    path("menyular/yangi/", views.MenyuCreate.as_view(), name="menyu_create"),
    path("menyular/<int:pk>/tahrirlash/", views.MenyuUpdate.as_view(), name="menyu_update"),
    path("menyular/<int:pk>/ochirish/", views.MenyuDelete.as_view(), name="menyu_delete"),

    path("menyular/<int:menyu_pk>/", views.YozuvList.as_view(), name="yozuv_list"),
    path("menyular/<int:menyu_pk>/yangi/", views.YozuvCreate.as_view(), name="yozuv_create"),
    path("menyular/<int:menyu_pk>/<int:pk>/tahrirlash/", views.YozuvUpdate.as_view(), name="yozuv_update"),
    path("menyular/<int:menyu_pk>/<int:pk>/ochirish/", views.YozuvDelete.as_view(), name="yozuv_delete"),
]
