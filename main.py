# main.py
import os
import json
import base64
import io
import flet as ft
import qrcode
from PIL import Image
from pathlib import Path
from datetime import datetime

from database import DatabaseManager
from utils import ar, MONTHS, get_target_month
from pdf_generator import generate_qr_pdf

PINK = "#EC4899"
PURPLE = "#8B5CF6"
GREEN = "#10B981"
RED = "#EF4444"
AMBER = "#F59E0B"
BLUE = "#1E3A8A"
BG = "#FDF2F8"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PNG = os.path.join(BASE_DIR, "assets", "icon.png")


def make_qr_data_url(data, size=280):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def main(page: ft.Page):
    page.title = "مدير درس أبلة ولاء"
    page.bgcolor = BG
    page.padding = 0
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=PINK)

    db = DatabaseManager()
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    def make_header(title, color=PINK, back=None, actions=None):
        ctrls = []
        if back:
            ctrls.append(ft.IconButton(ft.Icons.ARROW_FORWARD, icon_color="white",
                                        tooltip=ar("رجوع"), on_click=back))
        ctrls.append(ft.Text(ar(title), size=20, weight=ft.FontWeight.BOLD,
                              color="white", expand=True))
        if actions:
            ctrls.extend(actions)
        return ft.Container(content=ft.Row(ctrls), bgcolor=color,
                            padding=ft.Padding.symmetric(horizontal=16, vertical=12))

    def snack(msg, color=GREEN):
        s = ft.SnackBar(content=ft.Text(ar(msg), color="white"), bgcolor=color)
        page.overlay.append(s)
        s.open = True
        page.update()

    def show_login():
        page.views.clear()
        pw = ft.TextField(label=ar("كلمة المرور"), password=True, can_reveal_password=True,
                           width=350, text_align=ft.TextAlign.CENTER,
                           border_color=PINK, focused_border_color=PURPLE, text_size=18)
        err = ft.Text("", color=RED, size=13)

        def do_login(e):
            if pw.value == "12345":
                show_home()
            else:
                err.value = ar("كلمة المرور غلط")
                page.update()

        pw.on_submit = do_login

        if os.path.exists(LOGO_PNG):
            logo_widget = ft.Image(src=LOGO_PNG, width=140, height=140,
                                    fit=ft.BoxFit.CONTAIN)
        else:
            logo_widget = ft.Icon(ft.Icons.SCHOOL, size=100, color=PINK)

        page.views.append(ft.View(
            route="/login", bgcolor=BG, padding=0,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[ft.Container(
                content=ft.Column([
                    logo_widget,
                    ft.Container(height=8),
                    ft.Text(ar("مدير درس أبلة ولاء"), size=30,
                            weight=ft.FontWeight.BOLD, color=PINK),
                    ft.Text(ar("سجّل دخولك للمتابعة"), size=14, color=TEXT_MUTED),
                    ft.Container(height=16), pw, err, ft.Container(height=8),
                    ft.Button(content=ft.Text(ar("دخول"), size=18, color="white"),
                              bgcolor=PINK, width=350, height=55, on_click=do_login,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))),
                    ft.Container(height=8),
                    ft.Text(ar("كلمة المرور: 12345"), size=11, color=TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                padding=40, bgcolor=CARD_BG, border_radius=24, width=430,
                shadow=ft.BoxShadow(blur_radius=30, spread_radius=2,
                                    color=ft.Colors.with_opacity(0.15, PINK)),
            )],
        ))
        page.update()

    def show_home():
        page.views.clear()
        tm, ty = get_target_month()
        st = db.get_all_students()
        paid = db.get_paid_student_ids(tm, ty)
        total = len(st)
        p = len(paid)
        u = total - p
        pct = int(p / max(total, 1) * 100)

        def stat(icon, lbl, val, col):
            return ft.Container(
                content=ft.Column([
                    ft.Text(icon, size=24),
                    ft.Text(str(val), size=24, weight=ft.FontWeight.BOLD, color=col),
                    ft.Text(ar(lbl), size=11, color=TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                padding=12, bgcolor=CARD_BG, border_radius=14, expand=True,
            )

        def abtn(icon, lbl, col, cb):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=28, color="white"),
                    ft.Text(ar(lbl), size=13, color="white", weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=col, padding=16, border_radius=14, expand=True,
                on_click=cb, ink=True,
            )

        def do_export(e):
            try:
                name = f"walaa_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                candidates = [
                    "/storage/emulated/0/Download",
                    os.path.expanduser("~/storage/downloads"),
                    os.path.expanduser("~"),
                ]
                target_dir = None
                for p_ in candidates:
                    try:
                        os.makedirs(p_, exist_ok=True)
                        target_dir = p_
                        break
                    except Exception:
                        continue
                if not target_dir:
                    target_dir = os.path.expanduser("~")
                path = os.path.join(target_dir, name)
                ok, msg = db.export_db(path)
                snack(f"✅ تم التصدير\n{path}" if ok else f"❌ {msg}",
                      GREEN if ok else RED)
            except Exception as ex:
                snack(f"❌ خطأ: {ex}", RED)

        def on_import_result(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            path = e.files[0].path
            try:
                ok, msg, errors = db.import_db(path)
                snack(msg if ok else f"خطأ: {msg}", GREEN if ok else RED)
                if ok:
                    show_home()
            except Exception as ex:
                snack(f"❌ {ex}", RED)

        file_picker.on_result = on_import_result

        import_btn = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.UPLOAD_FILE, size=24, color="white"),
                ft.Text(ar("استيراد .db"), size=13, color="white",
                        weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor=BLUE, padding=14, border_radius=14, expand=True,
            action=ft.PickFiles(file_picker, allow_multiple=False,
                                 allowed_extensions=["db"]),
            ink=True,
        )

        export_btn = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.DOWNLOAD, size=24, color="white"),
                ft.Text(ar("تصدير .db"), size=13, color="white",
                        weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor=GREEN, padding=14, border_radius=14, expand=True,
            on_click=do_export, ink=True,
        )

        header = make_header("مدير درس أبلة ولاء", PINK,
                              actions=[ft.IconButton(ft.Icons.EXIT_TO_APP,
                                                      icon_color="white",
                                                      on_click=lambda e: show_login())])

        month_card = ft.Container(content=ft.Column([
            ft.Text(ar("الشهر المطلوب دفعه الآن"), size=13, color=BLUE),
            ft.Text(ar(f"{MONTHS[tm-1]} {ty}"), size=22,
                    weight=ft.FontWeight.BOLD, color=BLUE),
            ft.Text(ar("(الدفع آخر الشهر عن الشهر السابق)"), size=11, color=BLUE),
        ], spacing=2), padding=14, bgcolor="#DBEAFE", border_radius=14)

        page.views.append(ft.View(
            route="/home", bgcolor=BG, padding=0,
            controls=[header, ft.Container(content=ft.Column([
                ft.Text(ar("💾 قاعدة البيانات"), size=16,
                        weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Container(height=4),
                ft.Row([import_btn, export_btn], spacing=8),
                ft.Container(height=16),
                month_card, ft.Container(height=8),
                ft.Row([stat("👥", "الطلاب", total, PINK),
                        stat("✅", "دفعوا", p, GREEN)], spacing=8),
                ft.Row([stat("❌", "لم يدفعوا", u, RED),
                        stat("📊", "النسبة", f"{pct}%", PURPLE)], spacing=8),
                ft.Container(height=16),
                ft.Text(ar("⚡ إجراءات سريعة"), size=16,
                        weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Container(height=4),
                ft.Row([abtn(ft.Icons.PEOPLE, "الطلاب", PURPLE,
                              lambda e: show_students()),
                        abtn(ft.Icons.ADD, "إضافة", PINK,
                              lambda e: show_add_student()),
                        abtn(ft.Icons.QR_CODE_SCANNER, "مسح QR", GREEN,
                              lambda e: show_scanner())], spacing=8),
                ft.Row([abtn(ft.Icons.PRINT, "طباعة", AMBER,
                              lambda e: show_printer()),
                        abtn(ft.Icons.BAR_CHART, "تقارير", BLUE,
                              lambda e: show_reports()),
                        abtn(ft.Icons.ARROW_BACK, "خروج", TEXT_MUTED,
                              lambda e: show_login())], spacing=8),
            ], spacing=4, scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True),
            ],
        ))
        page.update()

    def show_students():
        page.views.clear()
        tm, ty = get_target_month()
        students = db.get_all_students()
        paid_ids = db.get_paid_student_ids(tm, ty)

        def row(s, is_paid):
            def manage(e):
                show_student_detail(s['id'])
            return ft.Container(
                content=ft.Row([
                    ft.Container(width=5, bgcolor=GREEN if is_paid else RED,
                                  border_radius=2),
                    ft.Column([
                        ft.Text(ar(s['name']), size=14,
                                weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text(f"{s['code']} • {int(s['fee'])} ج",
                                size=11, color=TEXT_MUTED),
                    ], spacing=1, expand=True),
                    ft.Button(ar("إدارة"), bgcolor=PURPLE, on_click=manage,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=8))),
                ], spacing=8),
                bgcolor=CARD_BG, padding=10, border_radius=10,
            )

        items = []
        if not students:
            items.append(ft.Text(ar("لا يوجد طلاب"), size=15, color=TEXT_MUTED))
        else:
            by_grade = {}
            for s in students:
                by_grade.setdefault(s['year'], []).append(s)
            for grade in sorted(by_grade.keys()):
                arr = by_grade[grade]
                ps = [s for s in arr if s['id'] in paid_ids]
                us = [s for s in arr if s['id'] not in paid_ids]
                items.append(ft.Container(content=ft.Row([
                    ft.Text(ar(f"📚 {grade}"), size=15,
                            weight=ft.FontWeight.BOLD, color=PINK, expand=True),
                    ft.Text(ar(f"✅ {len(ps)} ❌ {len(us)}"),
                            size=12, color=TEXT_MUTED),
                ]), bgcolor="#FCE7F3", padding=10, border_radius=8))
                if ps:
                    items.append(ft.Container(content=ft.Text(
                        ar(f"✅ دفعوا ({len(ps)})"), size=13,
                        weight=ft.FontWeight.BOLD, color=GREEN),
                        bgcolor=ft.Colors.with_opacity(0.15, GREEN),
                        padding=8, border_radius=6))
                    for s in sorted(ps, key=lambda x: x['name']):
                        items.append(row(s, True))
                if us:
                    items.append(ft.Container(content=ft.Text(
                        ar(f"❌ لم يدفعوا ({len(us)})"), size=13,
                        weight=ft.FontWeight.BOLD, color=RED),
                        bgcolor=ft.Colors.with_opacity(0.15, RED),
                        padding=8, border_radius=6))
                    for s in sorted(us, key=lambda x: x['name']):
                        items.append(row(s, False))

        header = make_header("الطلاب", PURPLE,
                              back=lambda e: show_home(),
                              actions=[ft.IconButton(ft.Icons.ADD, icon_color="white",
                                                      on_click=lambda e: show_add_student())])

        page.views.append(ft.View(
            route="/students", bgcolor=BG, padding=0,
            controls=[header, ft.Container(content=ft.Column(items, spacing=6,
                                                              scroll=ft.ScrollMode.AUTO,
                                                              expand=True),
                                            padding=12, expand=True)],
        ))
        page.update()

    def show_add_student():
        page.views.clear()
        name = ft.TextField(label=ar("اسم الطالب"), width=500)
        year = ft.TextField(label=ar("الصف"), width=500)
        fee = ft.TextField(label=ar("الرسوم"), value="120",
                            width=500, keyboard_type=ft.KeyboardType.NUMBER)
        phone = ft.TextField(label=ar("التليفون"), width=500)
        err = ft.Text("", color=RED, size=13)

        def save(e):
            n = (name.value or "").strip()
            y = (year.value or "").strip()
            if not n or not y:
                err.value = ar("❌ اكتب الاسم والصف")
                page.update()
                return
            try:
                f = float(fee.value or 0)
            except ValueError:
                f = 0
            db.add_student(n, y, f, (phone.value or "").strip())
            snack("✅ تم الحفظ")
            show_students()

        page.views.append(ft.View(
            route="/add", bgcolor=BG, padding=0,
            controls=[make_header("إضافة طالب", PINK,
                                   back=lambda e: show_home()),
                      ft.Container(content=ft.Column([
                          name, year, fee, phone, err, ft.Container(height=10),
                          ft.Row([
                              ft.Button(ar("حفظ"), bgcolor=GREEN, expand=True,
                                        height=50, on_click=save,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=12))),
                              ft.Button(ar("إلغاء"), bgcolor=TEXT_MUTED,
                                        expand=True, height=50,
                                        on_click=lambda e: show_home(),
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=12))),
                          ], spacing=10),
                      ], spacing=10, scroll=ft.ScrollMode.AUTO),
                          padding=20, bgcolor=CARD_BG, border_radius=16,
                          width=550),
                      ],
        ))
        page.update()

    def show_student_detail(sid):
        page.views.clear()
        s = db.get_student_by_id(sid)
        if not s:
            show_students()
            return
        tm, ty = get_target_month()
        payments = db.get_payments_for_student(sid, ty)
        paid_months = {p['month'] for p in payments}
        total = sum(p['amount'] for p in payments)

        payload = json.dumps({"code": s['code'], "name": s['name'],
                              "year": s['year'], "fee": s['fee']},
                             ensure_ascii=False)
        qr_url = make_qr_data_url(payload, 280)

        def toggle(m):
            def h(e):
                db.toggle_payment(sid, m, ty, s['fee'])
                show_student_detail(sid)
            return h

        month_rows = []
        for start in range(1, 13, 4):
            row_items = []
            for m in range(start, min(start+4, 13)):
                is_p = m in paid_months
                is_t = (m == tm)
                col = GREEN if is_p else (AMBER if is_t else "#D1D5DB")
                lbl = f"{MONTHS[m-1]}\n{'✓' if is_p else ('مطلوب' if is_t else '—')}"
                row_items.append(ft.Container(
                    content=ft.Text(ar(lbl), size=11,
                                    color="white" if (is_p or is_t) else TEXT_DARK,
                                    text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.BOLD),
                    bgcolor=col, padding=8, border_radius=8, expand=True,
                    on_click=toggle(m), ink=True, height=60,
                    alignment=ft.alignment.center,
                ))
            month_rows.append(ft.Row(row_items, spacing=6))

        def show_qr(e):
            def close(e2):
                dlg.open = False
                page.update()
            dlg = ft.AlertDialog(
                title=ft.Text(ar("كود QR"), color=PINK),
                content=ft.Column([
                    ft.Text(ar(s['name']), size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(s['code'], size=11, color=TEXT_MUTED),
                    ft.Image(src=qr_url, width=280, height=280),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6, tight=True),
                actions=[ft.TextButton(ar("إغلاق"), on_click=close)],
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        info = ft.Container(content=ft.Column([
            ft.Text(ar(f"الكود: {s['code']}"), size=12, color=TEXT_MUTED),
            ft.Text(ar(f"الصف: {s['year']}"), size=14,
                    weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            ft.Text(ar(f"الرسوم: {int(s['fee'])} ج/شهر"), size=14, color=PINK),
        ], spacing=4), padding=14, bgcolor=CARD_BG, border_radius=12)

        header = make_header(s['name'], PINK, back=lambda e: show_students(),
                              actions=[
                                  ft.IconButton(ft.Icons.QR_CODE, icon_color="white",
                                                on_click=show_qr),
                              ])

        page.views.append(ft.View(
            route="/detail", bgcolor=BG, padding=0,
            controls=[header, ft.Container(content=ft.Column([
                info, ft.Container(height=8),
                ft.Text(ar(f"💰 مدفوعات {ty}"), size=15,
                        weight=ft.FontWeight.BOLD, color=PINK),
                *month_rows,
                        ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                padding=16, expand=True),
            ],
        ))
        page.update()

    def show_scanner():
        page.views.clear()
        header = make_header("مسح QR", GREEN, back=lambda e: show_home())
        page.views.append(ft.View(
            route="/scan", bgcolor=BG, padding=0,
            controls=[header, ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.PHOTO_CAMERA_OUTLINED, size=100, color=TEXT_MUTED),
                ft.Container(height=16),
                ft.Text(ar("📷 ميزة الكاميرا قيد التطوير"),
                        size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Container(height=8),
                ft.Text(ar("ستكون متاحة في التحديث القادم"),
                        size=13, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                ft.Button(ar("رجوع"), bgcolor=GREEN, width=200, height=50,
                          on_click=lambda e: show_home(),
                          style=ft.ButtonStyle(
                              shape=ft.RoundedRectangleBorder(radius=12))),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER, spacing=8,
                expand=True),
                padding=16, expand=True,
            )],
        ))
        page.update()

    def show_printer():
        page.views.clear()
        years = db.get_all_years()
        grade_dd = ft.Dropdown(
            label=ar("الصف"),
            options=[ft.dropdown.Option("كل الصفوف")] +
                    [ft.dropdown.Option(y) for y in years],
            value="كل الصفوف", width=350,
        )
        status_dd = ft.Dropdown(
            label=ar("حالة الدفع"),
            options=[ft.dropdown.Option("الكل"),
                     ft.dropdown.Option("المدفوعين فقط"),
                     ft.dropdown.Option("غير المدفوعين فقط")],
            value="الكل", width=350,
        )
        cards = ft.TextField(label=ar("عدد الكروت/صفحة"), value="9",
                              width=200, keyboard_type=ft.KeyboardType.NUMBER)
        result = ft.Text("", size=12, color=TEXT_DARK)

        def gen(e):
            try:
                students = db.get_all_students()
                if grade_dd.value != "كل الصفوف":
                    students = [s for s in students if s['year'] == grade_dd.value]
                tm, ty = get_target_month()
                paid = db.get_paid_student_ids(tm, ty)
                if status_dd.value == "المدفوعين فقط":
                    students = [s for s in students if s['id'] in paid]
                elif status_dd.value == "غير المدفوعين فقط":
                    students = [s for s in students if s['id'] not in paid]
                if not students:
                    result.value = ar("❌ لا يوجد طلاب")
                    result.color = RED
                    page.update()
                    return
                try:
                    pp = max(1, min(int(cards.value or 9), 100))
                except Exception:
                    pp = 9
                success, path = generate_qr_pdf(students, pp, paid_ids=paid)
                if success:
                    result.value = ar(f"✅ تم ({len(students)} طالب، {pp} كارت/صفحة)\n{path}")
                    result.color = GREEN
                else:
                    result.value = ar(f"❌ فشل: {path}")
                    result.color = RED
                page.update()
            except Exception as ex:
                result.value = ar(f"❌ خطأ: {ex}")
                result.color = RED
                page.update()

        page.views.append(ft.View(
            route="/printer", bgcolor=BG, padding=0,
            controls=[make_header("طباعة PDF", AMBER, back=lambda e: show_home()),
                      ft.Container(content=ft.Column([
                          ft.Text(ar("1️⃣ الصف"), size=14,
                                  weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                          grade_dd,
                          ft.Text(ar("2️⃣ حالة الدفع"), size=14,
                                  weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                          status_dd,
                          ft.Text(ar("3️⃣ عدد الكروت/صفحة"), size=14,
                                  weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                          cards,
                          ft.Text(ar("💡 4-6 كروت = QR أكبر | 30 كارت = QR أصغر"),
                                  size=11, color=TEXT_MUTED),
                          ft.Container(height=10),
                          ft.Button(ar("📄 توليد PDF"), bgcolor=AMBER,
                                    width=300, height=55, on_click=gen,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=12))),
                          ft.Container(height=10), result,
                      ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                          padding=20, expand=True),
                      ],
        ))
        page.update()

    def show_reports():
        page.views.clear()
        tm, ty = get_target_month()
        students = db.get_all_students()
        paid = db.get_paid_student_ids(tm, ty)
        by_grade = {}
        for s in students:
            by_grade.setdefault(s['year'], []).append(s)

        sections = []
        for g in sorted(by_grade.keys()):
            arr = by_grade[g]
            ps = [s for s in arr if s['id'] in paid]
            us = [s for s in arr if s['id'] not in paid]
            sections.append(ft.Container(content=ft.Row([
                ft.Text(ar(g), size=14, weight=ft.FontWeight.BOLD,
                        color=PURPLE, expand=True),
                ft.Text(f"✅ {len(ps)}  ❌ {len(us)}", size=13, color=TEXT_DARK),
            ]), bgcolor=CARD_BG, padding=12, border_radius=10))

        page.views.append(ft.View(
            route="/reports", bgcolor=BG, padding=0,
            controls=[make_header(f"تقرير {MONTHS[tm-1]} {ty}", BLUE,
                                   back=lambda e: show_home()),
                      ft.Container(content=ft.Column([
                          ft.Row([
                              ft.Container(content=ft.Column([
                                  ft.Text(str(len(students)), size=24,
                                          weight=ft.FontWeight.BOLD, color=PINK),
                                  ft.Text(ar("الطلاب"), size=11, color=TEXT_MUTED),
                              ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                  bgcolor=CARD_BG, padding=12, border_radius=10,
                                  expand=True),
                              ft.Container(content=ft.Column([
                                  ft.Text(str(len(paid)), size=24,
                                          weight=ft.FontWeight.BOLD, color=GREEN),
                                  ft.Text(ar("دفعوا"), size=11, color=TEXT_MUTED),
                              ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                  bgcolor=CARD_BG, padding=12, border_radius=10,
                                  expand=True),
                              ft.Container(content=ft.Column([
                                  ft.Text(str(len(students)-len(paid)), size=24,
                                          weight=ft.FontWeight.BOLD, color=RED),
                                  ft.Text(ar("لم يدفعوا"), size=11, color=TEXT_MUTED),
                              ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                  bgcolor=CARD_BG, padding=12, border_radius=10,
                                  expand=True),
                          ], spacing=8),
                          ft.Container(height=16),
                          ft.Text(ar("📊 التفصيل حسب الصف"), size=15,
                                  weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                          *sections,
                      ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                          padding=16, expand=True),
                      ],
        ))
        page.update()

    show_login()


if __name__ == "__main__":
    ft.run(main)
