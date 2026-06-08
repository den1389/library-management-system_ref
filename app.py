"""
Library Management System — Flask Web UI
Запуск: python app.py  →  http://localhost:5000
"""
from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import uuid

from src.models.user import UserRole
from src.services.library_service import (
    LibraryService, LibraryException,
    BookNotAvailableError, UserBlockedError, BorrowLimitExceededError,
    BookNotFoundError, UserNotFoundError, LoanNotFoundError
)
from src.services.fine_strategy import StandardFineStrategy, ProgressiveFineStrategy
from src.storage.in_memory import (
    InMemoryBookRepository, InMemoryUserRepository,
    InMemoryLoanRepository, InMemoryNotificationRepository,
)

app = Flask(__name__)
app.secret_key = "library-demo-secret"

# ── Глобальний сервіс (in-memory) ────────────────────────────────────────────
svc = LibraryService(
    book_repo=InMemoryBookRepository(),
    user_repo=InMemoryUserRepository(),
    loan_repo=InMemoryLoanRepository(),
    notification_repo=InMemoryNotificationRepository(),
    fine_strategy=StandardFineStrategy(),
)

# ── Наповнення тестовими даними ──────────────────────────────────────────────
def seed():
    books_data = [
        ("Чистий код", "Роберт Мартін", "978-5-496-00487-0", 2008, "Програмування"),
        ("Python Cookbook", "Девід Бізлі", "978-1-449-34037-7", 2013, "Програмування"),
        ("Паттерни проєктування", "Банда чотирьох", "978-0-201-63361-0", 1994, "Архітектура"),
        ("Чистий архітектор", "Роберт Мартін", "978-0-13-468599-1", 2017, "Архітектура"),
        ("Рефакторинг", "Мартін Фаулер", "978-0-13-468495-6", 2018, "Програмування"),
        ("Алгоритми", "Сєджвік Вейн", "978-0-32-157351-3", 2011, "CS"),
        ("Системний дизайн", "Алекс Сюй", "978-1-736-04934-6", 2020, "Архітектура"),
    ]
    users_data = [
        ("Денис Студент", "denys@uni.edu", UserRole.READER),
        ("Оксана Читач", "oksana@uni.edu", UserRole.READER),
        ("Марія Бібліотекар", "lib@library.ua", UserRole.LIBRARIAN),
    ]
    for t, a, i, y, g in books_data:
        try: svc.add_book(t, a, i, y, g)
        except: pass
    for n, e, r in users_data:
        try: svc.register_user(n, e, r)
        except: pass

seed()

# ── HTML ШАБЛОН ──────────────────────────────────────────────────────────────
HTML = '''<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Library Management System</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0f0f13;--bg2:#17171e;--bg3:#1e1e28;
  --card:#22222e;--card2:#2a2a38;
  --border:#2e2e3e;--border2:#3a3a50;
  --text:#e8e8f0;--text2:#9898b0;--text3:#5a5a70;
  --blue:#4f8ef7;--blue2:#3a7af0;--blue-bg:#1a2540;
  --green:#3ecf7a;--green-bg:#0d2318;
  --orange:#f59e3a;--orange-bg:#2a1a08;
  --red:#f05a5a;--red-bg:#2a0f0f;
  --purple:#a78bfa;--purple-bg:#1e1530;
  --radius:12px;--radius-sm:8px;
}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:14px}

/* NAV */
nav{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 2rem;display:flex;align-items:center;gap:0;position:sticky;top:0;z-index:100;height:56px}
.nav-brand{font-family:'DM Serif Display',serif;font-size:1.2rem;color:var(--blue);margin-right:2rem;white-space:nowrap}
.nav-brand span{color:var(--text2);font-family:'DM Sans',sans-serif;font-size:0.75rem;font-weight:400;margin-left:0.5rem}
.nav-links{display:flex;gap:0.25rem;flex:1}
.nav-link{padding:0.4rem 0.9rem;border-radius:var(--radius-sm);color:var(--text2);text-decoration:none;font-size:0.85rem;font-weight:500;transition:all .15s}
.nav-link:hover{color:var(--text);background:var(--bg3)}
.nav-link.active{color:var(--blue);background:var(--blue-bg)}
.nav-stats{display:flex;gap:1rem;margin-left:auto}
.nav-stat{font-size:0.75rem;color:var(--text3)}
.nav-stat strong{color:var(--text);font-weight:600}

/* LAYOUT */
.container{max-width:1100px;margin:0 auto;padding:2rem 1.5rem}
.page-header{margin-bottom:1.5rem}
.page-title{font-family:'DM Serif Display',serif;font-size:1.6rem;color:var(--text)}
.page-sub{color:var(--text2);font-size:0.85rem;margin-top:0.25rem}

/* FLASH */
.flash{padding:0.75rem 1rem;border-radius:var(--radius-sm);margin-bottom:1rem;font-size:0.85rem;font-weight:500;border:1px solid}
.flash-ok{background:var(--green-bg);color:var(--green);border-color:#1a4a2a}
.flash-err{background:var(--red-bg);color:var(--red);border-color:#4a1a1a}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem;transition:border-color .15s}
.card:hover{border-color:var(--border2)}
.card-title{font-weight:600;margin-bottom:1rem;color:var(--text);display:flex;align-items:center;gap:0.5rem}
.card-title .icon{width:20px;height:20px;background:var(--blue-bg);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:11px}

/* GRID */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}

/* STAT CARDS */
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem}
.stat-val{font-family:'DM Serif Display',serif;font-size:2rem;font-weight:400;line-height:1}
.stat-label{font-size:0.75rem;color:var(--text2);margin-top:0.4rem;font-weight:500;text-transform:uppercase;letter-spacing:.05em}
.stat-blue .stat-val{color:var(--blue)}
.stat-green .stat-val{color:var(--green)}
.stat-orange .stat-val{color:var(--orange)}
.stat-red .stat-val{color:var(--red)}

/* TABLE */
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:0.85rem}
th{text-align:left;padding:0.6rem 0.75rem;color:var(--text3);font-weight:600;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--border)}
td{padding:0.65rem 0.75rem;border-bottom:1px solid var(--border);vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--bg3)}

/* BADGES */
.badge{display:inline-flex;align-items:center;gap:0.3rem;padding:0.2rem 0.55rem;border-radius:20px;font-size:0.72rem;font-weight:600;letter-spacing:.02em}
.badge::before{content:'';width:6px;height:6px;border-radius:50%;background:currentColor}
.b-green{background:var(--green-bg);color:var(--green)}
.b-blue{background:var(--blue-bg);color:var(--blue)}
.b-orange{background:var(--orange-bg);color:var(--orange)}
.b-red{background:var(--red-bg);color:var(--red)}
.b-purple{background:var(--purple-bg);color:var(--purple)}
.b-gray{background:var(--bg3);color:var(--text3)}

/* FORMS */
.form-group{margin-bottom:1rem}
label{display:block;font-size:0.78rem;font-weight:600;color:var(--text2);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:.04em}
input,select{width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.6rem 0.75rem;color:var(--text);font-family:inherit;font-size:0.875rem;outline:none;transition:border-color .15s}
input:focus,select:focus{border-color:var(--blue)}
select option{background:var(--bg3)}

/* BUTTONS */
.btn{display:inline-flex;align-items:center;gap:0.4rem;padding:0.5rem 1rem;border-radius:var(--radius-sm);border:none;font-family:inherit;font-size:0.825rem;font-weight:600;cursor:pointer;text-decoration:none;transition:all .15s}
.btn-primary{background:var(--blue2);color:#fff}
.btn-primary:hover{background:var(--blue);transform:translateY(-1px)}
.btn-success{background:#1a4a2a;color:var(--green)}
.btn-success:hover{background:#1e5530}
.btn-danger{background:#3a1010;color:var(--red)}
.btn-danger:hover{background:#4a1414}
.btn-ghost{background:transparent;color:var(--text2);border:1px solid var(--border)}
.btn-ghost:hover{background:var(--bg3);color:var(--text)}
.btn-sm{padding:0.3rem 0.65rem;font-size:0.75rem}
.btn-row{display:flex;gap:0.5rem;flex-wrap:wrap}

/* BOOK CARD */
.book-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;display:flex;flex-direction:column;gap:0.5rem;transition:all .15s}
.book-card:hover{border-color:var(--blue);transform:translateY(-2px)}
.book-title{font-weight:600;font-size:0.9rem;line-height:1.3}
.book-author{font-size:0.78rem;color:var(--text2)}
.book-meta{display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;margin-top:auto}
.book-genre{font-size:0.72rem;background:var(--bg3);color:var(--text3);padding:0.15rem 0.45rem;border-radius:4px}

/* USER CARD */
.user-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1rem}
.user-name{font-weight:600;margin-bottom:0.25rem}
.user-email{font-size:0.78rem;color:var(--text2);margin-bottom:0.5rem}
.user-info{display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center}

/* LOAN CARD */
.loan-row{display:grid;grid-template-columns:2fr 1.5fr 1.5fr 1fr auto;gap:0.75rem;align-items:center;padding:0.75rem;background:var(--card);border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:0.5rem}

/* EMPTY */
.empty{text-align:center;padding:3rem;color:var(--text3)}
.empty-icon{font-size:2.5rem;margin-bottom:0.75rem}
.empty-text{font-size:0.875rem}

/* FINE BAR */
.fine-bar{height:6px;background:var(--bg3);border-radius:3px;margin-top:0.4rem;overflow:hidden}
.fine-fill{height:100%;border-radius:3px;background:var(--orange);transition:width .3s}
.fine-fill.danger{background:var(--red)}

@media(max-width:700px){
  .grid-2,.grid-3,.grid-4{grid-template-columns:1fr}
  .loan-row{grid-template-columns:1fr;gap:0.5rem}
  nav{padding:0 1rem}
}
</style>
</head>
<body>

<nav>
  <div class="nav-brand">📚 LibraryMS <span>v1.0</span></div>
  <div class="nav-links">
    <a href="/" class="nav-link {{ 'active' if page=='home' }}">Головна</a>
    <a href="/books" class="nav-link {{ 'active' if page=='books' }}">Книги</a>
    <a href="/users" class="nav-link {{ 'active' if page=='users' }}">Читачі</a>
    <a href="/loans" class="nav-link {{ 'active' if page=='loans' }}">Видачі</a>
  </div>
  <div class="nav-stats">
    <div class="nav-stat"><strong>{{ stats.total_books }}</strong> книг</div>
    <div class="nav-stat"><strong>{{ stats.active_loans }}</strong> видач</div>
  </div>
</nav>

<div class="container">
  {% for cat, msg in get_flashed_messages(with_categories=True) %}
    <div class="flash {{ 'flash-ok' if cat=='success' else 'flash-err' }}">{{ msg }}</div>
  {% endfor %}
  {% block content %}{% endblock %}
</div>
</body></html>'''

HOME_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header">
  <div class="page-title">Панель управління</div>
  <div class="page-sub">Library Management System — In-Memory архітектура, GoF патерни, 239 тестів</div>
</div>

<div class="grid-4" style="margin-bottom:1.5rem">
  <div class="stat-card stat-blue">
    <div class="stat-val">{{ stats.total_books }}</div>
    <div class="stat-label">Книг у фонді</div>
  </div>
  <div class="stat-card stat-green">
    <div class="stat-val">{{ stats.available_books }}</div>
    <div class="stat-label">Доступних</div>
  </div>
  <div class="stat-card stat-orange">
    <div class="stat-val">{{ stats.active_loans }}</div>
    <div class="stat-label">Активних видач</div>
  </div>
  <div class="stat-card stat-red">
    <div class="stat-val">{{ stats.overdue_loans }}</div>
    <div class="stat-label">Прострочених</div>
  </div>
</div>

<div class="grid-2">
  <div class="card">
    <div class="card-title">Останні видачі</div>
    {% if loans %}
      <table>
        <thead><tr><th>Книга</th><th>Читач</th><th>Статус</th></tr></thead>
        <tbody>
        {% for loan in loans[:5] %}
          {% set book = books_map.get(loan.book_id) %}
          {% set user = users_map.get(loan.user_id) %}
          <tr>
            <td>{{ book.title if book else '—' }}</td>
            <td>{{ user.name if user else '—' }}</td>
            <td>
              {% if loan.status.value == 'active' %}<span class="badge b-blue">Активна</span>
              {% elif loan.status.value == 'overdue' %}<span class="badge b-red">Прострочено</span>
              {% elif loan.status.value == 'returned' %}<span class="badge b-gray">Повернуто</span>
              {% endif %}
            </td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% else %}
      <div class="empty"><div class="empty-text">Немає видач</div></div>
    {% endif %}
  </div>

  <div class="card">
    <div class="card-title">Швидкі дії</div>
    <div style="display:flex;flex-direction:column;gap:0.6rem">
      <a href="/books/add" class="btn btn-primary">➕ Додати книгу</a>
      <a href="/users/add" class="btn btn-ghost">👤 Додати читача</a>
      <a href="/loans/new" class="btn btn-ghost">📖 Видати книгу</a>
      <a href="/loans" class="btn btn-ghost">📋 Всі видачі</a>
    </div>
    <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border)">
      <div style="font-size:0.75rem;color:var(--text3);margin-bottom:0.5rem">ТЕХНОЛОГІЧНИЙ СТЕК</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.4rem">
        <span class="badge b-blue">Python 3.11</span>
        <span class="badge b-green">239 тестів</span>
        <span class="badge b-purple">91.1% coverage</span>
        <span class="badge b-orange">SonarCloud ✅</span>
      </div>
    </div>
  </div>
</div>
""")

BOOKS_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header" style="display:flex;align-items:center;justify-content:space-between">
  <div>
    <div class="page-title">Каталог книг</div>
    <div class="page-sub">{{ books|length }} книг у фонді</div>
  </div>
  <a href="/books/add" class="btn btn-primary">➕ Додати книгу</a>
</div>

<div class="grid-3">
{% for b in books %}
  <div class="book-card">
    <div class="book-title">{{ b.title }}</div>
    <div class="book-author">{{ b.author }}, {{ b.year }}</div>
    <div class="book-meta">
      <span class="book-genre">{{ b.genre }}</span>
      {% if b.status.value == 'available' %}<span class="badge b-green">Доступна</span>
      {% elif b.status.value == 'borrowed' %}<span class="badge b-orange">Видана</span>
      {% elif b.status.value == 'reserved' %}<span class="badge b-blue">Зарезервована</span>
      {% else %}<span class="badge b-gray">{{ b.status.value }}</span>{% endif %}
    </div>
    {% if b.reservation_queue %}
      <div style="font-size:0.72rem;color:var(--text3)">Черга: {{ b.reservation_queue|length }} осіб</div>
    {% endif %}
  </div>
{% else %}
  <div class="empty" style="grid-column:1/-1">
    <div class="empty-icon">📚</div>
    <div class="empty-text">Немає книг. <a href="/books/add" style="color:var(--blue)">Додати першу</a></div>
  </div>
{% endfor %}
</div>
""")

ADD_BOOK_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header">
  <div class="page-title">Додати книгу</div>
</div>
<div style="max-width:480px">
  <div class="card">
    <form method="POST">
      <div class="form-group"><label>Назва</label><input name="title" required placeholder="Чистий код"></div>
      <div class="form-group"><label>Автор</label><input name="author" required placeholder="Роберт Мартін"></div>
      <div class="form-group"><label>ISBN</label><input name="isbn" required placeholder="978-..."></div>
      <div class="grid-2">
        <div class="form-group"><label>Рік</label><input name="year" type="number" required value="2024"></div>
        <div class="form-group"><label>Жанр</label><input name="genre" required placeholder="Програмування"></div>
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Зберегти</button>
        <a href="/books" class="btn btn-ghost">Скасувати</a>
      </div>
    </form>
  </div>
</div>
""")

USERS_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header" style="display:flex;align-items:center;justify-content:space-between">
  <div>
    <div class="page-title">Читачі</div>
    <div class="page-sub">{{ users|length }} зареєстрованих</div>
  </div>
  <a href="/users/add" class="btn btn-primary">➕ Додати читача</a>
</div>
<div class="grid-3">
{% for u in users %}
  <div class="user-card">
    <div class="user-name">{{ u.name }}</div>
    <div class="user-email">{{ u.email }}</div>
    <div class="user-info">
      {% if u.role.value == 'librarian' %}<span class="badge b-purple">Бібліотекар</span>
      {% else %}<span class="badge b-blue">Читач</span>{% endif %}
      {% if u.status.value == 'active' %}<span class="badge b-green">Активний</span>
      {% elif u.status.value == 'blocked' %}<span class="badge b-red">Заблокований</span>{% endif %}
      {% if u.fine_amount > 0 %}<span class="badge b-orange">{{ u.fine_amount }} грн</span>{% endif %}
    </div>
    {% if u.fine_amount > 0 %}
      <div class="fine-bar"><div class="fine-fill {{ 'danger' if u.fine_amount >= 40 else '' }}" style="width:{{ [u.fine_amount/50*100, 100]|min }}%"></div></div>
    {% endif %}
    <div style="margin-top:0.5rem;font-size:0.75rem;color:var(--text3)">
      Книг: {{ u.borrowed_books|length }} / 5
    </div>
    {% if u.status.value == 'blocked' %}
      <form method="POST" action="/users/{{ u.id }}/unblock" style="margin-top:0.5rem">
        <button class="btn btn-success btn-sm">Розблокувати</button>
      </form>
    {% elif u.fine_amount > 0 %}
      <form method="POST" action="/users/{{ u.id }}/pay" style="margin-top:0.5rem;display:flex;gap:0.4rem">
        <input name="amount" type="number" step="0.01" value="{{ u.fine_amount }}" style="width:90px">
        <button class="btn btn-ghost btn-sm">Сплатити</button>
      </form>
    {% endif %}
  </div>
{% endfor %}
</div>
""")

ADD_USER_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header"><div class="page-title">Додати читача</div></div>
<div style="max-width:480px">
  <div class="card">
    <form method="POST">
      <div class="form-group"><label>Ім'я</label><input name="name" required placeholder="Іван Франко"></div>
      <div class="form-group"><label>Email</label><input name="email" type="email" required placeholder="ivan@uni.edu"></div>
      <div class="form-group"><label>Роль</label>
        <select name="role">
          <option value="reader">Читач</option>
          <option value="librarian">Бібліотекар</option>
        </select>
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Зберегти</button>
        <a href="/users" class="btn btn-ghost">Скасувати</a>
      </div>
    </form>
  </div>
</div>
""")

LOANS_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header" style="display:flex;align-items:center;justify-content:space-between">
  <div>
    <div class="page-title">Видачі</div>
    <div class="page-sub">{{ loans|length }} записів</div>
  </div>
  <a href="/loans/new" class="btn btn-primary">📖 Видати книгу</a>
</div>

{% if loans %}
<div class="table-wrap">
<table>
  <thead><tr><th>Книга</th><th>Читач</th><th>Видано</th><th>Повернути до</th><th>Статус</th><th>Дії</th></tr></thead>
  <tbody>
  {% for loan in loans %}
    {% set book = books_map.get(loan.book_id) %}
    {% set user = users_map.get(loan.user_id) %}
    <tr>
      <td><strong>{{ book.title if book else '—' }}</strong></td>
      <td>{{ user.name if user else '—' }}</td>
      <td style="color:var(--text2)">{{ loan.borrowed_at.strftime('%d.%m.%Y') }}</td>
      <td style="color:{{ 'var(--red)' if loan.is_overdue() else 'var(--text2)' }}">
        {{ loan.due_date.strftime('%d.%m.%Y') }}
        {% if loan.is_overdue() %}<span class="badge b-red" style="margin-left:4px">+{{ loan.days_overdue() }}д</span>{% endif %}
      </td>
      <td>
        {% if loan.status.value == 'active' %}<span class="badge b-blue">Активна</span>
        {% elif loan.status.value == 'overdue' %}<span class="badge b-red">Прострочено</span>
        {% elif loan.status.value == 'returned' %}<span class="badge b-gray">Повернуто</span>{% endif %}
      </td>
      <td>
        {% if loan.status.value in ['active','overdue'] %}
        <form method="POST" action="/loans/{{ loan.id }}/return" style="display:inline">
          <button class="btn btn-success btn-sm">Повернути</button>
        </form>
        {% if loan.can_extend() %}
        <form method="POST" action="/loans/{{ loan.id }}/extend" style="display:inline;margin-left:4px">
          <button class="btn btn-ghost btn-sm">+7 днів</button>
        </form>
        {% endif %}
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
</div>
{% else %}
  <div class="empty"><div class="empty-icon">📋</div><div class="empty-text">Немає видач</div></div>
{% endif %}
""")

NEW_LOAN_TMPL = HTML.replace("{% block content %}{% endblock %}", """
<div class="page-header"><div class="page-title">Видати книгу</div></div>
<div style="max-width:480px">
  <div class="card">
    <form method="POST">
      <div class="form-group"><label>Читач</label>
        <select name="user_id" required>
          <option value="">— оберіть читача —</option>
          {% for u in users %}
            {% if u.status.value == 'active' and u.role.value == 'reader' %}
              <option value="{{ u.id }}">{{ u.name }} ({{ u.borrowed_books|length }}/5 книг)</option>
            {% endif %}
          {% endfor %}
        </select>
      </div>
      <div class="form-group"><label>Книга</label>
        <select name="book_id" required>
          <option value="">— оберіть книгу —</option>
          {% for b in books %}
            {% if b.status.value == 'available' %}
              <option value="{{ b.id }}">{{ b.title }} — {{ b.author }}</option>
            {% endif %}
          {% endfor %}
        </select>
      </div>
      <div class="form-group"><label>Термін (днів)</label>
        <select name="days">
          <option value="7">7 днів</option>
          <option value="14" selected>14 днів</option>
          <option value="21">21 день</option>
          <option value="30">30 днів</option>
        </select>
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Видати</button>
        <a href="/loans" class="btn btn-ghost">Скасувати</a>
      </div>
    </form>
  </div>
</div>
""")

# ── Хелпери ──────────────────────────────────────────────────────────────────
def get_stats():
    return svc.get_statistics()

def books_map():
    return {b.id: b for b in svc.list_all_books()}

def users_map():
    return {u.id: u for u in svc._users.find_all()}

# ── Маршрути ─────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    loans = svc.get_active_loans() + [l for l in svc._loans.find_all() if l.status.value == 'returned']
    return render_template_string(HOME_TMPL, page="home",
        stats=get_stats(), loans=sorted(loans, key=lambda l: l.borrowed_at, reverse=True),
        books_map=books_map(), users_map=users_map())

@app.route("/books")
def books():
    return render_template_string(BOOKS_TMPL, page="books",
        stats=get_stats(), books=svc.list_all_books())

@app.route("/books/add", methods=["GET","POST"])
def add_book():
    if request.method == "POST":
        try:
            svc.add_book(request.form["title"], request.form["author"],
                         request.form["isbn"], int(request.form["year"]), request.form["genre"])
            flash(f"Книгу «{request.form['title']}» додано!", "success")
            return redirect(url_for("books"))
        except LibraryException as e:
            flash(str(e), "error")
    return render_template_string(ADD_BOOK_TMPL, page="books", stats=get_stats())

@app.route("/users")
def users():
    return render_template_string(USERS_TMPL, page="users",
        stats=get_stats(), users=svc._users.find_all())

@app.route("/users/add", methods=["GET","POST"])
def add_user():
    if request.method == "POST":
        try:
            role = UserRole.LIBRARIAN if request.form["role"] == "librarian" else UserRole.READER
            svc.register_user(request.form["name"], request.form["email"], role)
            flash(f"Читача «{request.form['name']}» зареєстровано!", "success")
            return redirect(url_for("users"))
        except LibraryException as e:
            flash(str(e), "error")
    return render_template_string(ADD_USER_TMPL, page="users", stats=get_stats())

@app.route("/users/<uid>/unblock", methods=["POST"])
def unblock_user(uid):
    try:
        u = svc.unblock_user(uid)
        flash(f"{u.name} — розблоковано!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("users"))

@app.route("/users/<uid>/pay", methods=["POST"])
def pay_fine(uid):
    try:
        amount = float(request.form["amount"])
        paid = svc.pay_fine(uid, amount)
        flash(f"Сплачено {paid} грн штрафу!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("users"))

@app.route("/loans")
def loans():
    all_loans = sorted(svc._loans.find_all(), key=lambda l: l.borrowed_at, reverse=True)
    return render_template_string(LOANS_TMPL, page="loans",
        stats=get_stats(), loans=all_loans,
        books_map=books_map(), users_map=users_map())

@app.route("/loans/new", methods=["GET","POST"])
def new_loan():
    if request.method == "POST":
        try:
            loan = svc.borrow_book(request.form["user_id"], request.form["book_id"],
                                    int(request.form["days"]))
            bk = books_map().get(loan.book_id)
            flash(f"Книгу «{bk.title if bk else ''}» видано!", "success")
            return redirect(url_for("loans"))
        except (UserBlockedError, BorrowLimitExceededError, BookNotAvailableError, LibraryException) as e:
            flash(str(e), "error")
    return render_template_string(NEW_LOAN_TMPL, page="loans",
        stats=get_stats(), users=svc._users.find_all(), books=svc.list_all_books())

@app.route("/loans/<lid>/return", methods=["POST"])
def return_loan(lid):
    try:
        loan = svc._loans.find_by_id(lid)
        if loan:
            result = svc.return_book(loan.user_id, loan.book_id)
            u = svc.get_user(loan.user_id)
            if result.fine_amount > 0:
                flash(f"Книгу повернуто. Нараховано штраф: {result.fine_amount} грн", "success")
            else:
                flash("Книгу повернуто вчасно. Штраф: 0 грн", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("loans"))

@app.route("/loans/<lid>/extend", methods=["POST"])
def extend_loan(lid):
    try:
        loan = svc._loans.find_by_id(lid)
        if loan:
            svc.extend_loan(loan.user_id, loan.book_id)
            flash("Термін продовжено на 7 днів!", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("loans"))

if __name__ == "__main__":
    print("\n  📚 Library Management System")
    print("  ─────────────────────────────")
    print("  Відкрий браузер: http://localhost:5000\n")
    app.run(debug=True, port=5000)
