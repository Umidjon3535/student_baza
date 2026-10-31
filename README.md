# Talabalar bazasi (Django)

## Ishga tushirish

```
pip install -r requirements.txt
python manage.py migrate
python manage.py namuna        # namunaviy ma'lumotlar + admin foydalanuvchi
python manage.py runserver
```

Brauzerda: http://127.0.0.1:8000 — ochiq sahifa. Boshqaruv paneli: `/boshqaruv/`, login: `admin`, parol: `admin123`

## Sahifalar

- Hamma uchun ochiq (faqat umumiy statistika, shaxsiy ma'lumotlarsiz):
  - `/` — bosh sahifa va slayder
  - `/sayt/natijalar/` — fakultet, kurs va semestr filtri, guruhlar reytingi
  - `/sayt/fakultetlar/` — qidiruv va har bir fakultet sahifasi
  - `/sayt/fanlar/` — qidiruv, saralash va har bir fan sahifasi
  - `/sayt/gpa/` — GPA kalkulyatori (kiritilgan ballar saqlanmaydi)
- Qolgan barcha sahifalar va Excel eksport — faqat login bilan.

## Internetga chiqarish

Serverda quyidagi muhit o'zgaruvchilari kerak:

```
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<uzun tasodifiy qiymat>
DJANGO_ALLOWED_HOSTS=sayt.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://sayt.uz
```

Keyin:

```
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py changepassword admin    # admin123 ochiq internetda qolmasin!
gunicorn config.wsgi
```

`DJANGO_DEBUG=0` bo'lganda sayt faqat HTTPS orqali ishlashi kerak (kirish cookie'lari shuni talab qiladi).
SQLite fayli saqlanib qoladigan server kerak; fayl tizimi vaqtinchalik bo'lgan xizmatlarda (masalan, Vercel) o'zgarishlar yo'qoladi.

## Jadvallar (ER modeli)

- **Fakultet** (nomi, dekan, telefon)
- **Guruh** (nomi, yo'nalish, kurs) → Fakultet (1:N)
- **Talaba** (F.I.Sh., jinsi, tug'ilgan sana, pasport, telefon, email, manzil, qabul yili, ta'lim shakli, holati) → Guruh (1:N)
- **Fan** (nomi, kredit, semestr, o'qituvchi)
- **Baho** (ball 0–100, sana) → Talaba va Fan (Talaba ↔ Fan M:N bog'lanish jadvali, `(talaba, fan)` unikal)

Baho hisoblash: 86–100 → 5, 71–85 → 4, 55–70 → 3, 0–54 → 2.
