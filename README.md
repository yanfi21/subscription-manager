# 📋 Subscription Manager

Веб-приложение для управления личными подписками. Помогает отслеживать регулярные платежи, контролировать расходы и не пропускать даты списаний.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

---

## Возможности

- ➕ Добавление, редактирование и удаление подписок
- 📅 Отслеживание дат списаний
- 💰 Учёт ежемесячных/ежегодных расходов
- 📊 Статистика по категориям подписок
- 🔔 Уведомления о предстоящих платежах
- 📱 Адаптивный дизайн (работает на телефонах и планшетах)

---

## 🚀 Быстрый старт

### Требования

- Python 3.8 или выше
- Git
- pip (менеджер пакетов Python)

### Установка и запуск

1. **Клонируйте репозиторий**

   ```bash
   git clone https://github.com/yanfi21/subscription-manager.git
   cd subscription-manager
   
2. **Создайте виртуальное окружение**
   
   ```bash
   python -m venv venv

3. **Активируйте виртуальное окружение**

   ```bash
   venv\Scripts\activate

4. **Установите зависимости**
   
   ```bash
   pip install -r requirements.txt

5. **Запустите приложение**

   ```bash
   python app.py

6. **Откройте в браузере**

   Перейдите по адресу: http://127.0.0.1:5000

### 🎯 Структура проекта

subscription-manager/
│
├── app.py                 # Главный файл приложения (маршруты и логика)
├── models.py              # Модели базы данных (SQLAlchemy)
├── requirements.txt       # Список зависимостей Python
├── .gitignore            # Игнорируемые Git файлы
├── README.md             # Документация
│
├── templates/            # HTML-шаблоны
│   ├── base.html        # Базовый шаблон
│   ├── index.html       # Главная страница
│   ├── add_subscription.html
│   └── ...
│
├── static/               # Статические файлы
│   ├── css/             # Стили
│   ├── js/              # Скрипты
│   └── images/          # Изображения
│
├── instance/             # Локальная БД (не в Git)
│   └── database.db      # SQLite база данных
│
└── __pycache__/         # Кэш Python (не в Git)

### 🛠 Используемые технологии

**Flask (веб-фреймворк)**

**SQLite (база данных)**

**HTML/CSS (интерфейс)**
   

