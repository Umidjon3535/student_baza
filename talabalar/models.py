from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse


def ball_bahosi(ball):
    if ball >= 86:
        return 5
    if ball >= 71:
        return 4
    if ball >= 55:
        return 3
    return 2


class Menyu(models.Model):
    nomi = models.CharField("Nomi", max_length=50)
    havola = models.CharField(
        "Havola (ixtiyoriy)",
        max_length=255,
        blank=True,
        validators=[RegexValidator(r"^(/|https?://)", "Havola / yoki http(s):// bilan boshlanishi kerak")],
    )
    ikonka = models.CharField(
        "Ikonka",
        max_length=50,
        default="bi-link-45deg",
        validators=[RegexValidator(r"^bi-[a-z0-9-]+$", "Format: bi-star")],
    )
    tartib = models.PositiveSmallIntegerField("Tartib", default=0)

    class Meta:
        verbose_name = "Menyu"
        verbose_name_plural = "Menyular"
        ordering = ["tartib", "nomi"]

    def __str__(self):
        return self.nomi


class Yozuv(models.Model):
    menyu = models.ForeignKey(Menyu, on_delete=models.PROTECT, related_name="yozuvlar", verbose_name="Menyu")
    sarlavha = models.CharField("Sarlavha", max_length=200)
    matn = models.TextField("Matn", blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Yozuv"
        verbose_name_plural = "Yozuvlar"
        ordering = ["-yaratilgan", "-id"]

    def __str__(self):
        return self.sarlavha


class Fakultet(models.Model):
    nomi = models.CharField("Nomi", max_length=150, unique=True)
    dekan = models.CharField("Dekan", max_length=150, blank=True)
    telefon = models.CharField("Telefon", max_length=20, blank=True)

    class Meta:
        verbose_name = "Fakultet"
        verbose_name_plural = "Fakultetlar"
        ordering = ["nomi"]

    def __str__(self):
        return self.nomi


class Guruh(models.Model):
    nomi = models.CharField("Guruh nomi", max_length=50, unique=True)
    fakultet = models.ForeignKey(Fakultet, on_delete=models.PROTECT, related_name="guruhlar", verbose_name="Fakultet")
    yonalish = models.CharField("Yo'nalish", max_length=150)
    kurs = models.PositiveSmallIntegerField(
        "Kurs", validators=[MinValueValidator(1), MaxValueValidator(6)], default=1
    )

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ["nomi"]

    def __str__(self):
        return self.nomi


class Fan(models.Model):
    nomi = models.CharField("Fan nomi", max_length=150, unique=True)
    kredit = models.PositiveSmallIntegerField("Kredit", default=4)
    semestr = models.PositiveSmallIntegerField(
        "Semestr", validators=[MinValueValidator(1), MaxValueValidator(12)], default=1
    )
    oqituvchi = models.CharField("O'qituvchi", max_length=150, blank=True)

    class Meta:
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"
        ordering = ["semestr", "nomi"]

    def __str__(self):
        return self.nomi


class Talaba(models.Model):
    JINS = [("E", "Erkak"), ("A", "Ayol")]
    TALIM_SHAKLI = [("grant", "Davlat granti"), ("kontrakt", "To'lov-kontrakt")]
    HOLAT = [
        ("oqiydi", "O'qiydi"),
        ("akademik", "Akademik ta'tilda"),
        ("chetlashtirilgan", "Chetlashtirilgan"),
        ("bitirgan", "Bitirgan"),
    ]

    familiya = models.CharField("Familiya", max_length=100)
    ism = models.CharField("Ism", max_length=100)
    otasining_ismi = models.CharField("Otasining ismi", max_length=100, blank=True)
    jinsi = models.CharField("Jinsi", max_length=1, choices=JINS)
    tugilgan_sana = models.DateField("Tug'ilgan sana")
    passport = models.CharField(
        "Pasport seriya/raqam",
        max_length=9,
        unique=True,
        validators=[RegexValidator(r"^[A-Z]{2}\d{7}$", "Format: AA1234567")],
    )
    telefon = models.CharField("Telefon", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    manzil = models.CharField("Manzil", max_length=255, blank=True)
    guruh = models.ForeignKey(Guruh, on_delete=models.PROTECT, related_name="talabalar", verbose_name="Guruh")
    qabul_yili = models.PositiveSmallIntegerField("Qabul yili")
    talim_shakli = models.CharField("Ta'lim shakli", max_length=10, choices=TALIM_SHAKLI, default="grant")
    holati = models.CharField("Holati", max_length=20, choices=HOLAT, default="oqiydi")
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Talaba"
        verbose_name_plural = "Talabalar"
        ordering = ["familiya", "ism"]

    def __str__(self):
        return self.toliq_ism

    @property
    def toliq_ism(self):
        return f"{self.familiya} {self.ism} {self.otasining_ismi}".strip()

    def get_absolute_url(self):
        return reverse("talaba_detail", args=[self.pk])

    def ortacha_ball(self):
        return self.baholar.aggregate(models.Avg("ball"))["ball__avg"]

    @property
    def gpa(self):
        """Kredit bilan tortilgan o'rtacha baho (2-5 shkala); baho bo'lmasa None."""
        baholar = self.baholar.all()
        kredit = sum(b.fan.kredit for b in baholar)
        if not kredit:
            return None
        return sum(b.baho * b.fan.kredit for b in baholar) / kredit


class Baho(models.Model):
    talaba = models.ForeignKey(Talaba, on_delete=models.CASCADE, related_name="baholar", verbose_name="Talaba")
    fan = models.ForeignKey(Fan, on_delete=models.PROTECT, related_name="baholar", verbose_name="Fan")
    ball = models.PositiveSmallIntegerField("Ball (0-100)", validators=[MaxValueValidator(100)])
    sana = models.DateField("Sana")

    class Meta:
        verbose_name = "Baho"
        verbose_name_plural = "Baholar"
        ordering = ["-sana"]
        constraints = [models.UniqueConstraint(fields=["talaba", "fan"], name="talaba_fan_unique")]

    def __str__(self):
        return f"{self.talaba} — {self.fan}: {self.ball}"

    @property
    def baho(self):
        return ball_bahosi(self.ball)
