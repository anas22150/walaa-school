# utils.py
from datetime import datetime

MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
          'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

GRADES = [
    'الأول الابتدائي', 'الثاني الابتدائي', 'الثالث الابتدائي',
    'الرابع الابتدائي', 'الخامس الابتدائي', 'السادس الابتدائي',
    'الأول الإعدادي', 'الثاني الإعدادي', 'الثالث الإعدادي',
    'الأول الثانوي', 'الثاني الثانوي', 'الثالث الثانوي'
]


def get_target_month():
    now = datetime.now()
    m = now.month - 1
    y = now.year
    if m == 0:
        m = 12
        y = now.year - 1
    return m, y


def calc_months_owed(first_seen, target_month, target_year):
    if not first_seen:
        return target_month
    try:
        if isinstance(first_seen, str):
            fs = datetime.fromisoformat(first_seen.split('.')[0].replace(' ', 'T'))
        else:
            fs = first_seen
        if fs.year > target_year:
            return 0
        start = 1 if fs.year < target_year else fs.month
        return max(0, target_month - start + 1)
    except Exception:
        return target_month


def ar(text):
    if text is None:
        return ""
    return str(text)
