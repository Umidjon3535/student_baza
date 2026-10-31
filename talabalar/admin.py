from django.contrib import admin

from .models import Baho, Fakultet, Fan, Guruh, Menyu, Talaba, Yozuv


def holat_amali(kalit, nomi):
    @admin.action(description=f"Holatini \"{nomi}\" qilish")
    def amal(modeladmin, request, queryset):
        soni = queryset.update(holati=kalit)
        modeladmin.message_user(request, f"{soni} ta talabaning holati o'zgartirildi")

    amal.__name__ = f"holat_{kalit}"
    return amal


@admin.register(Menyu)
class MenyuAdmin(admin.ModelAdmin):
    list_display = ["nomi", "havola", "ikonka", "tartib"]
    search_fields = ["nomi"]


@admin.register(Yozuv)
class YozuvAdmin(admin.ModelAdmin):
    list_display = ["sarlavha", "menyu", "yaratilgan"]
    list_filter = ["menyu"]
    search_fields = ["sarlavha", "matn"]


@admin.register(Fakultet)
class FakultetAdmin(admin.ModelAdmin):
    list_display = ["nomi", "dekan", "telefon"]
    search_fields = ["nomi"]


@admin.register(Guruh)
class GuruhAdmin(admin.ModelAdmin):
    list_display = ["nomi", "fakultet", "yonalish", "kurs"]
    list_filter = ["fakultet", "kurs"]
    search_fields = ["nomi", "yonalish"]


@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ["nomi", "kredit", "semestr", "oqituvchi"]
    search_fields = ["nomi"]


class BahoInline(admin.TabularInline):
    model = Baho
    extra = 0


@admin.register(Talaba)
class TalabaAdmin(admin.ModelAdmin):
    list_display = ["familiya", "ism", "guruh", "talim_shakli", "holati"]
    list_filter = ["guruh__fakultet", "guruh", "talim_shakli", "holati", "jinsi"]
    search_fields = ["familiya", "ism", "passport"]
    inlines = [BahoInline]
    actions = [holat_amali(kalit, nomi) for kalit, nomi in Talaba.HOLAT]


@admin.register(Baho)
class BahoAdmin(admin.ModelAdmin):
    list_display = ["talaba", "fan", "ball", "sana"]
    list_filter = ["fan"]
