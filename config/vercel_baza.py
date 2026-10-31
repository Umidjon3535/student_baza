"""Vercel'da loyiha fayllari faqat o'qish uchun: bazaning /tmp dagi nusxasi ishlatiladi."""
import shutil
import sqlite3


def bazani_tayyorlash(manba, nusxa, admin_parol_hash):
    """Nusxa bo'lmasa yaratadi. Repodagi parollar va sessiyalar ochiq, shuning uchun ularni almashtiradi."""
    if nusxa.exists():
        return
    vaqtinchalik = nusxa.with_suffix(".tayyorlanmoqda")
    shutil.copy(manba, vaqtinchalik)
    ulanish = sqlite3.connect(vaqtinchalik)
    with ulanish:
        # Hash berilmasa hech kim kira olmaydi ("!" Django'da yaroqsiz parol)
        ulanish.execute(
            "UPDATE auth_user SET password = CASE WHEN username = 'admin' THEN ? ELSE '!' END",
            (admin_parol_hash or "!",),
        )
        ulanish.execute("DELETE FROM django_session")
    ulanish.close()
    vaqtinchalik.replace(nusxa)
