from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, get_flashed_messages, make_response
from models import db, User, Subscription
from datetime import datetime, timedelta
import calendar
from functools import wraps
import os
import csv
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'ваш_секретный_ключ_смените_его'

UPLOAD_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Админ создан: admin / admin123")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Нет доступа', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/get-flash-messages')
def get_flash_messages_api():
    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        messages.append({'category': category, 'message': message})
    return jsonify(messages)

@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in ['ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            if user.avatar and os.path.exists(user.avatar[1:]):
                session['user_avatar'] = user.avatar
            else:
                session['user_avatar'] = None
            session['lang'] = 'ru'
            session['currency'] = user.currency
            return redirect(url_for('index'))
        flash('Неверное имя или пароль', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        
        if password != password2:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Имя пользователя должно быть не менее 3 символов', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Имя уже занято', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email уже используется', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_password':
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if not user.check_password(old_password):
                flash('Неверный текущий пароль', 'danger')
            elif new_password != confirm_password:
                flash('Новые пароли не совпадают', 'danger')
            elif len(new_password) < 4:
                flash('Пароль должен быть не менее 4 символов', 'danger')
            else:
                user.set_password(new_password)
                db.session.commit()
                flash('Пароль успешно изменён', 'success')
        
        elif action == 'update_settings':
            currency = request.form.get('currency', 'RUB')
            notifications = request.form.get('notifications') == 'on'
            
            user.currency = currency
            user.notifications_enabled = notifications
            db.session.commit()
            
            session['currency'] = currency
            flash('Настройки сохранены', 'success')
        
        elif action == 'update_avatar' and 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                if user.avatar and user.avatar != '/static/avatars/default-avatar.png':
                    old_file = user.avatar.replace('/static/avatars/', '')
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"user_{user.id}.{ext}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                user.avatar = f'/static/avatars/{filename}'
                db.session.commit()
                session['user_avatar'] = user.avatar
                flash('Аватар обновлён', 'success')
            else:
                flash('Неверный формат файла. Используйте PNG, JPG, JPEG, GIF', 'danger')
        
        elif action == 'delete_avatar':
            if user.avatar and user.avatar != '/static/avatars/default-avatar.png':
                old_file = user.avatar.replace('/static/avatars/', '')
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                if os.path.exists(old_path):
                    os.remove(old_path)
            user.avatar = None
            db.session.commit()
            session['user_avatar'] = None
            flash('Аватар удалён', 'info')
        
        return redirect(url_for('profile'))
    
    currency_symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€'
    }
    
    return render_template('profile.html', user=user, currency_symbols=currency_symbols)

@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    subscriptions = Subscription.query.filter_by(user_id=session['user_id']).order_by(Subscription.next_payment_date).all()
    
    currency_symbols = {'RUB': '₽', 'USD': '$', 'EUR': '€'}
    currency = user.currency if hasattr(user, 'currency') else 'RUB'
    symbol = currency_symbols.get(currency, '₽')
    
    total_monthly = 0
    total_yearly = 0
    
    for sub in subscriptions:
        if sub.status == 'active':
            if sub.period == 'month':
                total_monthly += sub.cost
                total_yearly += sub.cost * 12
            elif sub.period == 'year':
                total_monthly += sub.cost / 12
                total_yearly += sub.cost
            elif sub.period == 'week':
                total_monthly += sub.cost * 4.33
                total_yearly += sub.cost * 52
    
    session['currency'] = currency
    session['currency_symbol'] = symbol
    
    return render_template('index.html', 
                         subscriptions=subscriptions, 
                         total_monthly=round(total_monthly, 2),
                         total_yearly=round(total_yearly, 2),
                         symbol=symbol)

@app.route('/analytics')
@login_required
def analytics():
    user = User.query.get(session['user_id'])
    subscriptions = Subscription.query.filter_by(user_id=session['user_id']).all()
    
    currency_symbols = {'RUB': '₽', 'USD': '$', 'EUR': '€'}
    currency = user.currency if hasattr(user, 'currency') else 'RUB'
    symbol = currency_symbols.get(currency, '₽')
    
    category_totals = {}
    for sub in subscriptions:
        if sub.status == 'active':
            if sub.period == 'month':
                monthly_cost = sub.cost
            elif sub.period == 'year':
                monthly_cost = sub.cost / 12
            else:
                monthly_cost = sub.cost * 4.33
            
            if sub.category not in category_totals:
                category_totals[sub.category] = 0
            category_totals[sub.category] += monthly_cost
    
    categories = [{'name': k, 'total': round(v, 2)} for k, v in category_totals.items()]
    categories.sort(key=lambda x: x['total'], reverse=True)
    
    active_subscriptions = [s for s in subscriptions if s.status == 'active']
    for sub in active_subscriptions:
        if sub.period == 'month':
            sub.monthly_cost = sub.cost
        elif sub.period == 'year':
            sub.monthly_cost = sub.cost / 12
        else:
            sub.monthly_cost = sub.cost * 4.33
    
    top_subscriptions = sorted(active_subscriptions, key=lambda x: x.monthly_cost, reverse=True)[:5]
    top_subscriptions_data = [{'name': s.name, 'cost': round(s.monthly_cost, 2)} for s in top_subscriptions]
    
    return render_template('analytics.html', 
                         categories=categories,
                         top_subscriptions=top_subscriptions_data,
                         symbol=symbol)

@app.route('/export-excel')
@login_required
def export_excel():
    subscriptions = Subscription.query.filter_by(user_id=session['user_id']).order_by(Subscription.next_payment_date).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    if session.get('lang') == 'en':
        writer.writerow(['Name', 'Cost', 'Period', 'Next Payment Date', 'Category', 'Status'])
    else:
        writer.writerow(['Название', 'Стоимость', 'Период', 'Дата списания', 'Категория', 'Статус'])
    
    period_map = {'month': 'мес', 'year': 'год', 'week': 'нед'}
    period_map_en = {'month': 'month', 'year': 'year', 'week': 'week'}
    status_map = {'active': 'Активна', 'paused': 'Приостановлена', 'canceled': 'Отменена'}
    status_map_en = {'active': 'Active', 'paused': 'Paused', 'canceled': 'Canceled'}
    
    for sub in subscriptions:
        formatted_date = sub.next_payment_date.strftime('%d.%m.%Y')
        
        if session.get('lang') == 'en':
            writer.writerow([
                sub.name,
                sub.cost,
                period_map_en.get(sub.period, sub.period),
                formatted_date,
                sub.category,
                status_map_en.get(sub.status, sub.status)
            ])
        else:
            writer.writerow([
                sub.name,
                sub.cost,
                period_map.get(sub.period, sub.period),
                formatted_date,
                sub.category,
                status_map.get(sub.status, sub.status)
            ])
    
    output.seek(0)
    filename = f'subscriptions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    response = make_response(output.getvalue().encode('utf-8-sig'))
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-type'] = 'text/csv; charset=utf-8-sig'
    
    return response

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        subscription = Subscription(
            user_id=session['user_id'],
            name=request.form['name'],
            cost=float(request.form['cost']),
            period=request.form['period'],
            next_payment_date=datetime.strptime(request.form['next_payment_date'], '%Y-%m-%d').date(),
            category=request.form['category'],
            status=request.form['status']
        )
        db.session.add(subscription)
        db.session.commit()
        flash(f'Подписка "{request.form["name"]}" добавлена', 'success')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    subscription = Subscription.query.get_or_404(id)
    if subscription.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Чужая подписка', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        subscription.name = request.form['name']
        subscription.cost = float(request.form['cost'])
        subscription.period = request.form['period']
        subscription.next_payment_date = datetime.strptime(request.form['next_payment_date'], '%Y-%m-%d').date()
        subscription.category = request.form['category']
        subscription.status = request.form['status']
        db.session.commit()
        flash('Подписка обновлена', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', sub=subscription)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    subscription = Subscription.query.get_or_404(id)
    if subscription.user_id != session['user_id'] and not session.get('is_admin'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Unauthorized'}), 403
        flash('Нельзя удалить чужую подписку', 'danger')
        return redirect(url_for('index'))
    
    name = subscription.name
    db.session.delete(subscription)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'name': name}), 200
    
    flash(f'Подписка "{name}" удалена', 'info')
    return redirect(url_for('index'))

@app.route('/upcoming')
@login_required
def upcoming():
    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    upcoming_subs = Subscription.query.filter(
        Subscription.user_id == session['user_id'],
        Subscription.next_payment_date >= today,
        Subscription.next_payment_date <= week_later,
        Subscription.status == 'active'
    ).order_by(Subscription.next_payment_date).all()
    
    if session.get('lang') == 'en':
        empty_msg = "No upcoming payments in the next 7 days"
        title = "Upcoming Payments"
    else:
        empty_msg = "На ближайшие 7 дней списаний нет"
        title = "Ближайшие списания"
    
    return render_template('upcoming.html', upcoming=upcoming_subs, empty_msg=empty_msg, title=title)

@app.route('/calendar')
@login_required
def calendar_view():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    today = datetime.now().date()
    
    if not year or not month:
        year = today.year
        month = today.month
    
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    
    cal = calendar.monthcalendar(year, month)
    
    month_names_ru = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    month_names_en = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    if session.get('lang') == 'en':
        month_name = month_names_en[month]
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    else:
        month_name = month_names_ru[month]
        weekday_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    subscriptions = Subscription.query.filter_by(user_id=session['user_id'], status='active').all()
    
    payments_by_day = {}
    for sub in subscriptions:
        day = sub.next_payment_date.day
        if day not in payments_by_day:
            payments_by_day[day] = []
        payments_by_day[day].append(sub)
    
    return render_template('calendar.html', 
                         calendar=cal, 
                         month_name=month_name,
                         year=year,
                         month=month,
                         weekday_names=weekday_names,
                         payments_by_day=payments_by_day,
                         today=today)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)