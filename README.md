# 📚 Library Management System

[![CI/CD Pipeline](https://github.com/den1389/library-management-system_ref/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/den1389/library-management-system_ref/actions/workflows/ci-pipeline.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=https://github.com/den1389/library-management-system_ref&metric=alert_status)](https://sonarcloud.io/project/overview?id=library-management-system_ref)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=library-management-system_ref&metric=coverage)](https://sonarcloud.io/project/overview?id=library-management-system_ref)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=library-management-system_ref&metric=code_smells)](https://sonarcloud.io/project/overview?id=library-management-system_ref)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=library-management-system_ref&metric=bugs)](https://sonarcloud.io/project/overview?id=library-management-system_ref)

Система управління бібліотекою з In-Memory сховищем, GoF патернами, SOLID принципами та повним CI/CD пайплайном.

---

## 🏗️ Архітектура

```
src/
├── models/          # Доменні сутності (Book, User, Loan, Notification)
├── services/        # Бізнес-логіка (LibraryService, FineStrategy, EventBus)
├── storage/         # Інтерфейси репозиторіїв + In-Memory реалізації
└── utils/           # Допоміжні функції
tests/
├── unit/            # Модульні тести (моделі, стратегії, репозиторії)
└── integration/     # Інтеграційні тести (повні сценарії)
docs/diagrams/       # UML діаграми
.cursor/rules/       # AI Rules (architecture.md, testing_strategy.md)
.github/workflows/   # CI/CD пайплайн
```

## 🎯 GoF Патерни

### Strategy — Алгоритми нарахування штрафів

| Стратегія                 | Опис                        |
| ------------------------- | --------------------------- |
| `StandardFineStrategy`    | 0.50 грн/день               |
| `ProgressiveFineStrategy` | 0.50 → 1.00 → 2.00 грн/день |
| `FlatFineStrategy`        | Фіксовані 5.00 грн          |
| `WeeklyFineStrategy`      | 3.00 грн/тиждень            |

### Observer — Система сповіщень

- `EventBus` — центральний диспетчер подій
- `NotificationObserver` — створює сповіщення для користувачів
- Події: `book_returned`, `book_overdue`, `fine_charged`, `user_blocked`, `reservation_ready`, `loan_extended`

## 🚀 Швидкий старт

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Запустити тести
pytest -v

# 3. Запустити з покриттям
pytest --cov=src --cov-report=html:coverage_html --cov-report=xml:coverage.xml --junitxml=junit.xml -v

# 4. Переглянути звіт покриття
open coverage_html/index.html

# 5. Запустити в Docker
docker build -t library-system .
docker run library-system
```

## 📊 Quality Metrics

| Метрика          | Ціль       | Статус |
| ---------------- | ---------- | ------ |
| Code Coverage    | ≥ 70%      | ✅     |
| Кількість тестів | ≥ 200      | ✅     |
| Bugs             | 0          | ✅     |
| Vulnerabilities  | 0          | ✅     |
| Code Smells      | Рівень A/B | ✅     |

## 🔑 Бізнес-логіка

### Видача книги

1. Перевірка статусу користувача (не заблокований)
2. Перевірка ліміту позичань (макс. 5)
3. Перевірка суми штрафів (< 50 грн)
4. Перевірка доступності книги
5. Оновлення статусу книги та запис у базу

### Повернення книги

1. Пошук активної видачі
2. Розрахунок штрафу за прострочення (через Strategy)
3. Оновлення статусу книги
4. Обробка черги резервувань
5. Публікація подій (Observer)

### Блокування користувача

- Автоматично при штрафах ≥ 50 грн
- Вручну бібліотекарем

## 📋 Актори та ролі

- **Читач (Reader)**: позичання, повернення, резервування, перегляд
- **Бібліотекар (Librarian)**: все вище + управління книгами/користувачами

## ⚙️ CI/CD

Пайплайн (`.github/workflows/ci-pipeline.yml`) виконує:

1. **Build** — встановлення залежностей
2. **Test** — запуск 200+ тестів
3. **Coverage** — генерація HTML + XML звітів
4. **SonarCloud** — статичний аналіз якості
5. **Artifacts** — збереження junit.xml, coverage.xml, coverage_html/

### Захист гілки (Branch Protection)

- PR не може бути прийнятий, якщо пайплайн "червоний"
- Quality Gate SonarCloud має бути "зелений"
- Coverage ≥ 70% обов'язковий

## 📁 Структура репозиторію

```
.
├── src/                    # Вихідний код
├── tests/                  # 200+ тестів
├── docs/diagrams/          # UML діаграми
├── .cursor/rules/          # AI Skills (architecture.md, testing_strategy.md)
├── .github/workflows/      # CI/CD пайплайн
├── .cursorrules            # Глобальні правила для AI
├── Dockerfile              # Контейнеризація
├── pytest.ini              # Конфігурація тестів
├── setup.cfg               # Coverage конфігурація
├── sonar-project.properties # SonarQube конфігурація
├── requirements.txt        # Залежності
└── README.md               # Цей файл
```
