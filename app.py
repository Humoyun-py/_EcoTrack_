# app.py - TO'LIQ ECOVERSE BACKEND TIZIMI
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import random
from sqlalchemy import func
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eco-verse-2024-secret-key'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "ecoverse.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# DATABASE MODELLARI
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='child')
    coins = db.Column(db.Integer, default=0)
    energy = db.Column(db.Integer, default=100)
    streak = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(200), default='default.png')
    is_admin = db.Column(db.Boolean, default=False)
    last_daily_reset = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward_coins = db.Column(db.Integer, default=10)
    energy_cost = db.Column(db.Integer, default=10)
    difficulty = db.Column(db.String(20), default='easy')
    quiz_required = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    daily_reset = db.Column(db.Boolean, default=False)
    task_type = db.Column(db.String(20), default='regular')
    category = db.Column(db.String(50), default='eco')

class DailyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    task_1_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    task_2_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    task_3_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    quiz_1_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    task_1 = db.relationship('Task', foreign_keys=[task_1_id])
    task_2 = db.relationship('Task', foreign_keys=[task_2_id])
    task_3 = db.relationship('Task', foreign_keys=[task_3_id])
    quiz_1 = db.relationship('Task', foreign_keys=[quiz_1_id])

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(30), nullable=False)
    image_path = db.Column(db.String(200))
    energy_boost = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class EnergyPack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    energy_amount = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    equipped = db.Column(db.Boolean, default=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='inventory_items')
    item = db.relationship('Item', backref='inventory_items')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_path = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    views_count = db.Column(db.Integer, default=0)
    author = db.relationship('User', backref=db.backref('news_posts', lazy=True))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    announcement_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    author = db.relationship('User', backref=db.backref('announcements', lazy=True))

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    coins_earned = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    difficulty = db.Column(db.String(20), default='medium')
    user = db.relationship('User', backref='quiz_results')
    task = db.relationship('Task', backref='quiz_results')

class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='user_tasks')
    task = db.relationship('Task', backref='user_tasks')

class DailyProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    tasks_completed = db.Column(db.Integer, default=0)
    quizzes_completed = db.Column(db.Integer, default=0)
    coins_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='daily_progress')

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='achievements')

# Agar Notification modeli yo'q bo'lsa, app.py ga qo'shing
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='notifications')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def init_database():
    with app.app_context():
        try:
            db.drop_all()
            db.create_all()
            create_demo_data()
            print("✅ Database yangilandi!")
            
            create_daily_tasks()
            
        except Exception as e:
            print(f"❌ Database yangilashda xatolik: {e}")
            db.create_all()
            create_demo_data()
            print("✅ Database yaratildi!")
            create_daily_tasks()

def create_demo_data():
    demo_tasks = [
        # Kunlik topshiriqlar
        Task(title="Suv tejash", description="Bugun dush vaqtingizni 5 daqiqaga kamaytiring", reward_coins=15, energy_cost=8, difficulty="easy", quiz_required=False, daily_reset=True, task_type="daily", category="water"),
        Task(title="Energiya tejash", description="1 soat davomida keraksiz qurilmalarni o'chiring", reward_coins=20, energy_cost=10, difficulty="easy", quiz_required=False, daily_reset=True, task_type="daily", category="energy"),
        Task(title="Plastikni qayta ishlash", description="3 ta plastik idishni qayta ishlash uchun ajrating", reward_coins=25, energy_cost=12, difficulty="medium", quiz_required=False, daily_reset=True, task_type="daily", category="recycling"),
        
        # Doimiy topshiriqlar
        Task(title="Daraxt ekish", description="Yashil maydonga 1 ta daraxt eking", reward_coins=50, energy_cost=25, difficulty="hard", quiz_required=True, task_type="regular", category="planting"),
        Task(title="Kompost yaratish", description="Oziq-ovqat chiqindilaridan kompost tayyorlang", reward_coins=40, energy_cost=20, difficulty="medium", quiz_required=True, task_type="regular", category="composting"),
        Task(title="Velosiped haydash", description="1 kun davomida mashina o'rniga velosiped haydang", reward_coins=35, energy_cost=18, difficulty="medium", quiz_required=True, task_type="regular", category="transport"),
        
        # Test topshiriqlari
        Task(title="Ekologik bilim testi", description="Ekologiya haqidagi bilimingizni sinab ko'ring", reward_coins=30, energy_cost=15, difficulty="easy", quiz_required=True, task_type="quiz", category="knowledge"),
        Task(title="Qayta ishlash testi", description="Qayta ishlash qoidalarini bilasizmi?", reward_coins=45, energy_cost=22, difficulty="medium", quiz_required=True, task_type="quiz", category="recycling"),
        Task(title="Energiya tejash testi", description="Energiya tejash usullarini bilasizmi?", reward_coins=60, energy_cost=30, difficulty="hard", quiz_required=True, task_type="quiz", category="energy"),
    ]
    
    demo_items = [
        Item(name="Yashil Kepka", price=30, item_type="hat", image_path="images/hat_green.png"),
        Item(name="Ko'k Kepka", price=35, item_type="hat", image_path="images/hat_blue.png"),
        Item(name="Qizil Kepka", price=40, item_type="hat", image_path="images/hat_red.png"),
        Item(name="Yashil Futbolka", price=45, item_type="clothes", image_path="images/shirt_green.png"),
        Item(name="Ko'k Futbolka", price=50, item_type="clothes", image_path="images/shirt_blue.png"),
        Item(name="Qora Futbolka", price=55, item_type="clothes", image_path="images/shirt_black.png"),
        Item(name="Krossovka", price=60, item_type="shoes", image_path="images/shoes_sneakers.png"),
        Item(name="Qizil krossovka", price=65, item_type="shoes", image_path="images/shoes_red.png"),
        Item(name="Oq Krossovka", price=70, item_type="shoes", image_path="images/shoes_white.png"),    
        Item(name="Jins Shim", price=70, item_type="clothes", image_path="images/pants_jeans.png"),
        Item(name="Yashil Shim", price=75, item_type="clothes", image_path="images/pants_green.png"),
        Item(name="Rukzak", price=80, item_type="accessory", image_path="images/backpack.png"),
        Item(name="Quyosh ko'zoynak", price=85, item_type="accessory", image_path="images/sunglasses.png"),
        Item(name="Sport soati", price=90, item_type="accessory", image_path="images/sport_watch.png"),
    ]
    
    demo_energy_packs = [
        EnergyPack(name="Kichik Energiya Paketi", energy_amount=20, price=15, description="20 energiya"),
        EnergyPack(name="O'rta Energiya Paketi", energy_amount=50, price=35, description="50 energiya"),
        EnergyPack(name="Katta Energiya Paketi", energy_amount=100, price=60, description="100 energiya"),
    ]
    
    demo_users = [
        User(username='admin', email='admin@ecoverse.com', password_hash=generate_password_hash('admin123'), role='admin', coins=1000, is_admin=True),
        User(username='eco_bola', email='bola@ecoverse.com', password_hash=generate_password_hash('bola123'), role='child', coins=150),
        User(username='eco_katta', email='katta@ecoverse.com', password_hash=generate_password_hash('katta123'), role='adult', coins=80),
    ]
    
    demo_news = [
        News(
            title="EcoVerse yangi kunlik topshiriqlar bilan yangilandi!",
            content="Har kuni yangi ekologik topshiriqlar va testlar bilan tajribangizni boyiting!",
            category="yangilik",
            author_id=1,
            image_path="images/news_update.jpg"
        ),
        News(
            title="Yangi ekologik kiyimlar do'konda",
            content="Do'konimizda yangi ekologik toza materiallardan tayyorlangan kiyimlar paydo bo'ldi",
            category="yangilik",
            author_id=1,
            image_path="images/new_clothes.jpg"
        ),
    ]
    
    demo_announcements = [
        Announcement(
            title="Tizim yangilanishi",
            content="30-dekabr kuni soat 23:00 dan 31-dekabr soat 02:00 gacha tizimda texnik ishlar olib boriladi.",
            announcement_type="warning",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            author_id=1
        ),
        Announcement(
            title="Yangi yil aksiyasi",
            content="Yangi yil munosabati bilan barcha topshiriqlardan olinadigan coinlar 2 baravar oshirildi!",
            announcement_type="success", 
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=14),
            author_id=1
        )
    ]
    
    for user in demo_users:
        db.session.add(user)
    for task in demo_tasks:
        db.session.add(task)
    for item in demo_items:
        db.session.add(item)
    for energy_pack in demo_energy_packs:
        db.session.add(energy_pack)
    for news in demo_news:
        db.session.add(news)
    for announcement in demo_announcements:
        db.session.add(announcement)
    
    db.session.commit()

def create_daily_tasks():
    today = datetime.utcnow().date()
    
    existing_daily = DailyTask.query.filter_by(date=today).first()
    if existing_daily:
        return existing_daily
    
    daily_tasks = Task.query.filter_by(task_type='daily', is_active=True).all()
    quiz_tasks = Task.query.filter_by(task_type='quiz', is_active=True).all()
    
    if len(daily_tasks) >= 3 and len(quiz_tasks) >= 1:
        selected_daily = random.sample(daily_tasks, 3)
        selected_quiz = random.choice(quiz_tasks)
        
        new_daily = DailyTask(
            date=today,
            task_1_id=selected_daily[0].id,
            task_2_id=selected_daily[1].id,
            task_3_id=selected_daily[2].id,
            quiz_1_id=selected_quiz.id
        )
        
        db.session.add(new_daily)
        db.session.commit()
        print(f"✅ Kunlik topshiriqlar yaratildi: {today}")
        return new_daily
    
    return None

def get_todays_tasks():
    today = datetime.utcnow().date()
    daily_task = DailyTask.query.filter_by(date=today).first()
    
    if not daily_task:
        daily_task = create_daily_tasks()
    
    if daily_task:
        return {
            'daily_tasks': [daily_task.task_1, daily_task.task_2, daily_task.task_3],
            'daily_quiz': daily_task.quiz_1
        }
    return None

def load_questions_from_json():
    try:
        with open('ml_questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print("⚠️  ml_questions.json fayli topilmadi! Demo savollar ishlatiladi.")
        return create_demo_questions()
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON faylini o'qishda xatolik: {e}")
        return create_demo_questions()
    except Exception as e:
        print(f"⚠️  Xatolik: {e}")
        return create_demo_questions()

def create_demo_questions():
    return {
        "eco_questions": [
            {
                "id": 1,
                "question": "Plastik idishlarni qayta ishlash qaysi atrof-muhit muammosini yechishga yordam beradi?",
                "options": ["Havo ifloslanishi", "Suv ifloslanishi", "Tuproq ifloslanishi", "Shovqin ifloslanishi"],
                "correct_answer": 1,
                "category": "qayta ishlash",
                "difficulty": "easy",
                "explanation": "Plastik idishlar suv manbalarini ifloslantiradi, qayta ishlash bu muammoni kamaytiradi."
            },
            {
                "id": 2,
                "question": "Quyosh energiyasidan foydalanish qanday afzalliklarga ega?",
                "options": ["Havoni ifloslantiradi", "Qayta tiklanmaydigan manba", "Toza va bepul energiya", "Faqat kunduzi ishlaydi"],
                "correct_answer": 2,
                "category": "energy",
                "difficulty": "easy",
                "explanation": "Quyosh energiyasi toza, bepul va qayta tiklanadigan energiya manbaidir."
            },
            {
                "id": 3,
                "question": "Daraxtlar qanday ekologik ahamiyatga ega?",
                "options": ["Havoni ifloslantiradi", "Karbonat angidridni yutadi", "Suvni ifloslantiradi", "Tuproqni quriydi"],
                "correct_answer": 1,
                "category": "planting",
                "difficulty": "medium",
                "explanation": "Daraxtlar karbonat angidridni yutib, kislorod chiqaradi va havoni tozalaydi."
            },
            {
                "id": 4,
                "question": "Qaysi chiqindilar kompost qilish mumkin?",
                "options": ["Plastik idishlar", "Oziq-ovqat chiqindilari", "Metall bankalar", "Shisha idishlar"],
                "correct_answer": 1,
                "category": "composting",
                "difficulty": "medium",
                "explanation": "Oziq-ovqat chiqindilari kompost qilinishi mumkin, bu organik o'g'it hosil qiladi."
            },
            {
                "id": 5,
                "question": "Energiya tejashning eng samarali usuli qaysi?",
                "options": ["Har doim chiroqlarni yoqib qo'yish", "Energiya tejovchi qurilmalardan foydalanish", "Konditsionerni doim ishlatish", "Elektron qurilmalarni uxlatish rejimida qoldirish"],
                "correct_answer": 1,
                "category": "energy",
                "difficulty": "hard",
                "explanation": "Energiya tejovchi qurilmalar elektr energiyasini samarali ishlatishga yordam beradi."
            }
        ]
    }

def daily_reset_system():
    with app.app_context():
        today = datetime.utcnow().date()
        print(f"🔄 Kunlik yangilanish boshlandi: {today}")
        
        create_daily_tasks()
        
        users = User.query.all()
        for user in users:
            daily_progress = DailyProgress(
                user_id=user.id,
                date=today,
                tasks_completed=0,
                quizzes_completed=0,
                coins_earned=0
            )
            db.session.add(daily_progress)
            
            user.energy = min(100, user.energy + 50)
            user.last_daily_reset = datetime.utcnow()
        
        db.session.commit()
        print(f"✅ Kunlik yangilanish bajarildi: {today}")

def start_daily_scheduler():
    def scheduler():
        while True:
            now = datetime.utcnow()
            if now.hour == 0 and now.minute == 0:
                daily_reset_system()
                time.sleep(60)
            time.sleep(30)
    
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
    print("🕒 Kunlik yangilanish scheduler'i ishga tushdi")

def check_level_up(user):
    required_exp = user.level * 100
    if user.experience >= required_exp:
        user.level += 1
        user.experience = 0
        user.coins += user.level * 50
        return True
    return False

def reset_daily_tasks(user_id):
    today = datetime.utcnow().date()
    
    todays_tasks = get_todays_tasks()
    if todays_tasks:
        daily_task_ids = [task.id for task in todays_tasks['daily_tasks']] + [todays_tasks['daily_quiz'].id]
        
        for task_id in daily_task_ids:
            user_task = UserTask.query.filter_by(user_id=user_id, task_id=task_id).first()
            if user_task:
                if user_task.completed_at and user_task.completed_at.date() != today:
                    user_task.completed = False
                    user_task.completed_at = None
            else:
                new_user_task = UserTask(user_id=user_id, task_id=task_id)
                db.session.add(new_user_task)
    
    db.session.commit()

# YANGI: TOPSHIRIQ VA DO'KON FUNKSIYALARI
@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    """Topshiriqni bajarilgan deb belgilash"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Energiya tekshirish
        if current_user.energy < task.energy_cost:
            return jsonify({'success': False, 'error': f'Energiya yetarli emas! Kerak: {task.energy_cost}, Sizda: {current_user.energy}'})
        
        # Topshiriq allaqachon bajarilganligini tekshirish
        user_task = UserTask.query.filter_by(
            user_id=current_user.id, 
            task_id=task_id
        ).first()
        
        if user_task and user_task.completed:
            return jsonify({'success': False, 'error': 'Bu topshiriq allaqachon bajarilgan!'})
        
        # Energiya olib tashlash
        current_user.energy -= task.energy_cost
        
        # Coinlarni qo'shish
        current_user.coins += task.reward_coins
        
        # Tajriba qo'shish
        exp_gained = task.reward_coins // 2
        current_user.experience += exp_gained
        
        # Daraja yangilash
        while current_user.experience >= current_user.level * 100:
            current_user.experience -= current_user.level * 100
            current_user.level += 1
        
        # Topshiriqni bajarilgan deb belgilash
        if user_task:
            user_task.completed = True
            user_task.completed_at = datetime.utcnow()
        else:
            new_user_task = UserTask(
                user_id=current_user.id,
                task_id=task_id,
                completed=True,
                completed_at=datetime.utcnow()
            )
            db.session.add(new_user_task)
        
        # Kunlik progressni yangilash
        today = datetime.utcnow().date()
        daily_progress = DailyProgress.query.filter_by(
            user_id=current_user.id, 
            date=today
        ).first()
        
        if daily_progress:
            daily_progress.tasks_completed += 1
            daily_progress.coins_earned += task.reward_coins
        else:
            new_daily_progress = DailyProgress(
                user_id=current_user.id,
                date=today,
                tasks_completed=1,
                quizzes_completed=0,
                coins_earned=task.reward_coins
            )
            db.session.add(new_daily_progress)
        
        # Notification yaratish
        notification = Notification(
            user_id=current_user.id,
            title='✅ Topshiriq Bajarildi!',
            message=f'"{task.title}" topshirig\'i bajarildi! +{task.reward_coins} coin, +{exp_gained} tajriba',
            notification_type='task',
            is_read=False
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Topshiriq bajarildi! +{task.reward_coins} coin, +{exp_gained} tajriba',
            'new_coins': current_user.coins,
            'new_energy': current_user.energy,
            'new_level': current_user.level,
            'new_experience': current_user.experience
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# app.py ga quyidagi funksiyalarni qo'shing
# app.py ga quyidagi route'larni qo'shing yoki yangilang

@app.route('/buy_energy', methods=['POST'])
@login_required
def buy_energy():
    """Energiya sotib olish - YANGILANGAN VERSIYA"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Ma\'lumotlar yetarli emas!'})
        
        energy_amount = data.get('energy', 0)
        price = data.get('price', 0)
        
        if not energy_amount or not price:
            return jsonify({'success': False, 'error': 'Energiya miqdori yoki narx ko\'rsatilmagan!'})
        
        # Coinlarni tekshirish
        if current_user.coins < price:
            return jsonify({'success': False, 'error': f'Coin yetarli emas! Sizda {current_user.coins} coin bor, kerak: {price}'})
        
        # Coinlarni olib tashlash
        current_user.coins -= price
        
        # Energiyani qo'shish (maksimum 100)
        new_energy = min(100, current_user.energy + energy_amount)
        current_user.energy = new_energy
        
        # Notification yaratish
        notification = Notification(
            user_id=current_user.id,
            title='⚡ Energiya to\'ldirildi!',
            message=f'Siz {energy_amount} energiya sotib oldingiz! -{price} coin',
            notification_type='energy',
            is_read=False
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{energy_amount} energiya muvaffaqiyatli sotib olindi!',
            'new_coins': current_user.coins,
            'new_energy': current_user.energy
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Xatolik buy_energy da: {str(e)}")
        return jsonify({'success': False, 'error': f'Server xatosi: {str(e)}'})

@app.route('/buy_item/<int:item_id>', methods=['POST'])
@login_required
def buy_item(item_id):
    """Mahsulot sotib olish - YANGILANGAN VERSIYA"""
    try:
        item = Item.query.get_or_404(item_id)
        
        # Mahsulot faol emasligini tekshirish
        if not item.is_active:
            return jsonify({'success': False, 'error': 'Bu mahsulot hozir mavjud emas!'})
        
        # Coinlarni tekshirish
        if current_user.coins < item.price:
            return jsonify({'success': False, 'error': f'Coin yetarli emas! Sizda {current_user.coins} coin bor, kerak: {item.price}'})
        
        # Inventarda borligini tekshirish
        existing_item = Inventory.query.filter_by(
            user_id=current_user.id, 
            item_id=item_id
        ).first()
        
        if existing_item:
            return jsonify({'success': False, 'error': 'Sizda bu mahsulot allaqachon bor!'})
        
        # Coinlarni olib tashlash
        current_user.coins -= item.price
        
        # Energiya boost qo'shish
        new_energy = current_user.energy
        if item.energy_boost > 0:
            new_energy = min(100, current_user.energy + item.energy_boost)
            current_user.energy = new_energy
        
        # Inventarga qo'shish
        new_inventory = Inventory(
            user_id=current_user.id,
            item_id=item_id,
            equipped=False
        )
        db.session.add(new_inventory)
        
        # Notification yaratish
        notification = Notification(
            user_id=current_user.id,
            title='🛍️ Yangi mahsulot!',
            message=f'Siz {item.name} ni {item.price} coinga sotib oldingiz!',
            notification_type='shop',
            is_read=False
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{item.name} muvaffaqiyatli sotib olindi!' + 
                      (f' +{item.energy_boost} energiya' if item.energy_boost > 0 else ''),
            'new_coins': current_user.coins,
            'new_energy': current_user.energy
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Xatolik buy_item da: {str(e)}")
        return jsonify({'success': False, 'error': f'Server xatosi: {str(e)}'})

@app.route('/shop')
@login_required
def shop():
    """Do'kon sahifasi - YANGILANGAN VERSIYA"""
    try:
        items = Item.query.filter_by(is_active=True).all()
        
        return render_template('shop.html', 
                             user=current_user, 
                             items=items)
    except Exception as e:
        print(f"Shop route xatosi: {str(e)}")
        flash('Do\'kon yuklanmadi!', 'error')
        return redirect(url_for('dashboard'))


# ASOSIY ROUTE'LAR
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'adult':
            return redirect(url_for('dashboard_adult'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            today = datetime.now().date()
            if user.last_login:
                last_login_date = user.last_login.date()
                if last_login_date != today:
                    if (today - last_login_date).days == 1:
                        user.streak += 1
                        if user.streak % 7 == 0:
                            user.coins += 100
                            flash('7 kunlik ketma-ket tizimga kirish uchun 100 coin mukofoti!', 'success')
                    else:
                        user.streak = 1
            else:
                user.streak = 1
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=True)
            flash(f'Xush kelibsiz, {user.username}!', 'success')
            
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'adult':
                return redirect(url_for('dashboard_adult'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Login yoki parol noto\'g\'ri!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('Bu foydalanuvchi nomi band!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Bu email band!', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username, 
            email=email, 
            password_hash=hashed_password, 
            role=role,
            coins=100 if role == 'child' else 50, 
            energy=100, 
            streak=0
        )
        
        db.session.add(new_user)
        db.session.commit()
        flash('Hisob muvaffaqiyatli yaratildi! Iltimos, tizimga kiring.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    if current_user.role == 'adult':
        return redirect(url_for('dashboard_adult'))
    
    reset_daily_tasks(current_user.id)
    
    todays_tasks = get_todays_tasks()
    
    all_tasks = Task.query.filter_by(is_active=True).all()
    
    daily_tasks = [task for task in all_tasks if task.daily_reset]
    regular_tasks = [task for task in all_tasks if task.task_type == 'regular']
    quiz_tasks = [task for task in all_tasks if task.task_type == 'quiz']
    
    news_list = News.query.filter_by(status='active').order_by(News.created_at.desc()).limit(3).all()
    
    now = datetime.utcnow()
    announcements = Announcement.query.filter(
        Announcement.is_active == True,
        Announcement.start_date <= now,
        Announcement.end_date >= now
    ).order_by(Announcement.created_at.desc()).all()
    
    completed_tasks = UserTask.query.filter_by(user_id=current_user.id, completed=True).all()
    completed_task_ids = [ut.task_id for ut in completed_tasks]
    
    today = datetime.utcnow().date()
    daily_progress = DailyProgress.query.filter_by(user_id=current_user.id, date=today).first()
    
    items = Item.query.filter_by(is_active=True).limit(6).all()
    energy_packs = EnergyPack.query.filter_by(is_active=True).all()
    
    return render_template('dashboard_child.html', 
                         user=current_user, 
                         todays_tasks=todays_tasks,
                         daily_tasks=daily_tasks,
                         regular_tasks=regular_tasks,
                         quiz_tasks=quiz_tasks,
                         all_tasks=all_tasks,
                         news_list=news_list,
                         announcements=announcements,
                         items=items, 
                         energy_packs=energy_packs,
                         completed_task_ids=completed_task_ids,
                         daily_progress=daily_progress,
                         now=datetime.utcnow())

# QUIZ ROUTE'LARI
@app.route('/ml_quiz')
@login_required
def ml_quiz():
    task_id = request.args.get('task_id', type=int)
    difficulty = request.args.get('difficulty', '')
    task = None
    
    if task_id:
        task = Task.query.get(task_id)
        if task:
            difficulty = task.difficulty
    
    return render_template('ml_quiz.html', 
                         user=current_user, 
                         task=task, 
                         difficulty=difficulty)

@app.route('/ml/get_questions')
@login_required
def get_questions():
    try:
        data = load_questions_from_json()
        
        if 'eco_questions' not in data:
            return jsonify({'success': False, 'error': 'JSON faylda eco_questions topilmadi!'})
        
        all_questions = data['eco_questions']
        
        if len(all_questions) == 0:
            return jsonify({'success': False, 'error': 'JSON faylda savollar topilmadi!'})
        
        difficulty_filter = request.args.get('difficulty', '').lower()
        task_id = request.args.get('task_id', type=int)
        user_level = current_user.level
        
        if not difficulty_filter:
            if user_level <= 3:
                difficulty_filter = 'easy'
            elif user_level <= 6:
                difficulty_filter = 'medium'
            else:
                difficulty_filter = 'hard'
        
        if task_id:
            task = Task.query.get(task_id)
            if task:
                difficulty_filter = task.difficulty
        
        filtered_questions = []
        
        if difficulty_filter:
            difficulty_mapping = {
                'easy': ['easy', 'oson', 'oddiy'],
                'medium': ['medium', 'o\'rta', 'ortacha', 'middle'],
                'hard': ['hard', 'qiyin', 'murakkab', 'difficult']
            }
            
            target_difficulties = difficulty_mapping.get(difficulty_filter, [difficulty_filter])
            
            main_questions = [q for q in all_questions if q.get('difficulty', '').lower() in target_difficulties]
            
            if len(main_questions) < 5:
                remaining_needed = 5 - len(main_questions)
                
                if difficulty_filter == 'easy':
                    additional_questions = [q for q in all_questions if q.get('difficulty', '').lower() in difficulty_mapping['medium']]
                    additional_questions = additional_questions[:remaining_needed]
                    main_questions.extend(additional_questions)
                
                elif difficulty_filter == 'medium':
                    medium_count = min(4, len(main_questions))
                    easy_questions = [q for q in all_questions if q.get('difficulty', '').lower() in difficulty_mapping['easy']]
                    hard_questions = [q for q in all_questions if q.get('difficulty', '').lower() in difficulty_mapping['hard']]
                    
                    additional_easy = easy_questions[:1] if easy_questions else []
                    additional_hard = hard_questions[:1] if hard_questions else []
                    
                    main_questions = main_questions[:medium_count]
                    main_questions.extend(additional_easy)
                    main_questions.extend(additional_hard)
                
                elif difficulty_filter == 'hard':
                    additional_questions = [q for q in all_questions if q.get('difficulty', '').lower() in difficulty_mapping['medium']]
                    additional_questions = additional_questions[:remaining_needed]
                    main_questions.extend(additional_questions)
            
            filtered_questions = main_questions
            
            if len(filtered_questions) == 0:
                filtered_questions = all_questions
        
        selected_questions = random.sample(filtered_questions, min(5, len(filtered_questions)))
        
        return jsonify({
            'success': True,
            'questions': selected_questions,
            'total': len(selected_questions),
            'difficulty': difficulty_filter,
            'user_level': user_level,
            'source': 'ml_questions.json'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Savollarni yuklashda xatolik: {str(e)}'})

@app.route('/ml/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    try:
        data = request.get_json()
        results = data.get('results', [])
        score = data.get('score', 0)
        correct_count = data.get('correct_count', 0)
        total_questions = data.get('total_questions', 0)
        task_id = data.get('task_id', None)
        difficulty = data.get('difficulty', 'medium')
        
        base_coins = 20
        base_energy_cost = 15
        
        if difficulty == 'easy':
            coins_earned = base_coins + (correct_count * 2)
            energy_cost = base_energy_cost
            exp_gained = correct_count * 5
        elif difficulty == 'medium':
            coins_earned = base_coins + (correct_count * 3)
            energy_cost = base_energy_cost + 5
            exp_gained = correct_count * 8
        else:
            coins_earned = base_coins + (correct_count * 5)
            energy_cost = base_energy_cost + 10
            exp_gained = correct_count * 12
        
        task = None
        if task_id:
            task = Task.query.get(task_id)
            if task:
                coins_earned += task.reward_coins
                if task.difficulty == 'easy':
                    coins_earned += 10
                elif task.difficulty == 'medium':
                    coins_earned += 15
                elif task.difficulty == 'hard':
                    coins_earned += 20
        
        if current_user.energy < energy_cost:
            return jsonify({
                'success': False,
                'error': f'Energiya yetarli emas! Sizda {current_user.energy} energiya bor, kerak: {energy_cost}'
            })
        
        current_user.coins += coins_earned
        current_user.energy = max(0, current_user.energy - energy_cost)
        current_user.experience += exp_gained
        
        level_up = check_level_up(current_user)
        
        quiz_result = QuizResult(
            user_id=current_user.id,
            score=score,
            correct_answers=correct_count,
            total_questions=total_questions,
            coins_earned=coins_earned,
            task_id=task_id,
            difficulty=difficulty
        )
        
        db.session.add(quiz_result)
        
        today = datetime.utcnow().date()
        daily_progress = DailyProgress.query.filter_by(user_id=current_user.id, date=today).first()
        if daily_progress:
            daily_progress.quizzes_completed += 1
            daily_progress.coins_earned += coins_earned
        
        db.session.commit()
        
        message = f'Test muvaffaqiyatli yakunlandi! {correct_count}/{total_questions} savolga to\'g\'ri javob berdingiz. {coins_earned} coin yutib oldingiz!'
        
        if level_up:
            message += f' Tabriklaymiz! Siz {current_user.level}-darajaga ko\'tarildingiz!'
        
        if task:
            message += f' "{task.title}" topshirig\'i uchun test tamomlandi!'
        
        return jsonify({
            'success': True,
            'score': score,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'coins_earned': coins_earned,
            'energy_used': energy_cost,
            'experience_gained': exp_gained,
            'new_coins': current_user.coins,
            'new_energy': current_user.energy,
            'new_experience': current_user.experience,
            'new_level': current_user.level,
            'level_up': level_up,
            'difficulty': difficulty,
            'task_completed': bool(task),
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Natijalarni saqlashda xatolik: {str(e)}'})

# QOLGAN ROUTE'LAR
@app.route('/start_task_quiz/<int:task_id>')
@login_required
def start_task_quiz(task_id):
    if current_user.role != 'child':
        flash('Faqat bolalar uchun!', 'error')
        return redirect(url_for('dashboard'))
    
    task = Task.query.get_or_404(task_id)
    
    if current_user.energy < task.energy_cost:
        flash(f'Energiya yetarli emas! Sizda {current_user.energy} energiya bor, kerak: {task.energy_cost}', 'error')
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('ml_quiz', task_id=task_id))

# app.py ga quyidagi hero route'ini qo'shing yoki yangilang

@app.route('/hero')
@login_required
def hero():
    """Hero sahifasi - YANGILANGAN VERSIYA"""
    try:
        # Foydalanuvchining inventaridagi barcha elementlar
        inventory_items = Inventory.query.filter_by(user_id=current_user.id).all()
        
        # Kiyilgan elementlar
        equipped_items = [item for item in inventory_items if item.equipped]
        
        # Turlarga qarab guruhlash
        clothes_items = [item for item in inventory_items if item.item.item_type == 'clothes']
        hat_items = [item for item in inventory_items if item.item.item_type == 'hat']
        shoe_items = [item for item in inventory_items if item.item.item_type == 'shoes']
        accessory_items = [item for item in inventory_items if item.item.item_type == 'accessory']
        
        # Kiyilgan elementlarni alohida guruhlash
        equipped_clothes = [item for item in clothes_items if item.equipped]
        equipped_hat = [item for item in hat_items if item.equipped]
        equipped_shoes = [item for item in shoe_items if item.equipped]
        equipped_accessory = [item for item in accessory_items if item.equipped]
        
        # Statistikalar
        user_tasks_completed = UserTask.query.filter_by(user_id=current_user.id, completed=True).count()
        quiz_results_count = QuizResult.query.filter_by(user_id=current_user.id).count()
        total_coins_earned = db.session.query(func.sum(QuizResult.coins_earned)).filter_by(user_id=current_user.id).scalar() or 0
        
        return render_template('hero.html', 
                             user=current_user,
                             inventory_items=inventory_items,
                             equipped_items=equipped_items,
                             clothes_items=clothes_items,
                             hat_items=hat_items,
                             shoe_items=shoe_items,
                             accessory_items=accessory_items,
                             equipped_clothes=equipped_clothes,
                             equipped_hat=equipped_hat,
                             equipped_shoes=equipped_shoes,
                             equipped_accessory=equipped_accessory,
                             user_tasks_completed=user_tasks_completed,
                             quiz_results_count=quiz_results_count,
                             total_coins_earned=total_coins_earned)
        
    except Exception as e:
        print(f"Hero route xatosi: {str(e)}")
        flash('Hero sahifasi yuklanmadi!', 'error')
        return redirect(url_for('dashboard'))

@app.route('/equip_item/<int:item_id>', methods=['POST'])
@login_required
def equip_item(item_id):
    """Elementni kiyish"""
    try:
        inventory_item = Inventory.query.filter_by(user_id=current_user.id, id=item_id).first()
        
        if not inventory_item:
            return jsonify({'success': False, 'error': 'Element topilmadi!'})
        
        item_type = inventory_item.item.item_type
        
        # Bir xil turdagi boshqa elementlarni echish
        same_type_items = Inventory.query.filter_by(user_id=current_user.id, equipped=True).join(Item).filter(Item.item_type == item_type).all()
        for item in same_type_items:
            item.equipped = False
        
        # Yangi elementni kiyish
        inventory_item.equipped = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{inventory_item.item.name} muvaffaqiyatli kiyildi!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Xatolik: {str(e)}'})

@app.route('/unequip_item/<int:item_id>', methods=['POST'])
@login_required
def unequip_item(item_id):
    """Elementni echish"""
    try:
        inventory_item = Inventory.query.filter_by(user_id=current_user.id, id=item_id).first()
        
        if not inventory_item:
            return jsonify({'success': False, 'error': 'Element topilmadi!'})
        
        if not inventory_item.equipped:
            return jsonify({'success': False, 'error': 'Bu element kiyilmagan!'})
        
        # Elementni echish
        inventory_item.equipped = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{inventory_item.item.name} muvaffaqiyatli echildi!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Xatolik: {str(e)}'})

# ADMIN ROUTE'LARI
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    total_users = User.query.count()
    total_tasks = Task.query.count()
    total_quiz_results = QuizResult.query.count()
    total_posts = News.query.count()
    total_child_users = User.query.filter_by(role='child').count()
    total_adult_users = User.query.filter_by(role='adult').count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_posts = News.query.order_by(News.created_at.desc()).limit(5).all()
    
    today = datetime.utcnow().date()
    daily_progress_today = DailyProgress.query.filter_by(date=today).all()
    total_tasks_today = sum(dp.tasks_completed for dp in daily_progress_today)
    total_quizzes_today = sum(dp.quizzes_completed for dp in daily_progress_today)
    
    return render_template('admin_dashboard.html', 
                         user=current_user,
                         total_users=total_users,
                         total_tasks=total_tasks,
                         total_quiz_results=total_quiz_results,
                         total_posts=total_posts,
                         total_child_users=total_child_users,
                         total_adult_users=total_adult_users,
                         recent_users=recent_users,
                         recent_posts=recent_posts,
                         total_tasks_today=total_tasks_today,
                         total_quizzes_today=total_quizzes_today)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin_users.html', user=current_user, users=users)

@app.route('/admin/tasks')
@login_required
def admin_tasks():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    tasks = Task.query.all()
    return render_template('admin_tasks.html', user=current_user, tasks=tasks)

@app.route('/admin/child')
@login_required
def admin_child():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    child_users = User.query.filter_by(role='child').all()
    tasks = Task.query.all()
    return render_template('admin_child.html', user=current_user, child_users=child_users, tasks=tasks)

@app.route('/admin/adult')
@login_required
def admin_adult():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    adult_users = User.query.filter_by(role='adult').all()
    return render_template('admin_adult.html', user=current_user, adult_users=adult_users)

@app.route('/admin/news')
@login_required
def admin_news():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    news_list = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin_news.html', user=current_user, news_list=news_list)

@app.route('/admin/announcements')
@login_required
def admin_announcements():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    now = datetime.utcnow()
    
    active_announcements_count = Announcement.query.filter(
        Announcement.start_date <= now,
        Announcement.end_date >= now,
        Announcement.is_active == True
    ).count()
    
    expired_announcements_count = Announcement.query.filter(
        Announcement.end_date < now
    ).count()
    
    return render_template('admin_announcements.html', 
                         user=current_user, 
                         announcements=announcements,
                         active_announcements_count=active_announcements_count,
                         expired_announcements_count=expired_announcements_count,
                         datetime=datetime)

@app.route('/admin/daily_tasks')
@login_required
def admin_daily_tasks():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    today = datetime.utcnow().date()
    daily_task = DailyTask.query.filter_by(date=today).first()
    all_daily_tasks = DailyTask.query.order_by(DailyTask.date.desc()).limit(7).all()
    
    return render_template('admin_daily_tasks.html', 
                         user=current_user, 
                         daily_task=daily_task,
                         all_daily_tasks=all_daily_tasks)

@app.route('/admin/shop')
@login_required
def admin_shop():
    if not current_user.is_admin:
        flash('Sizga admin huquqi berilmagan!', 'error')
        return redirect(url_for('dashboard'))
    
    items = Item.query.all()
    energy_packs = EnergyPack.query.all()
    
    return render_template('admin_shop.html', 
                         user=current_user, 
                         items=items,
                         energy_packs=energy_packs)

# YANGI ADMIN API ROUTE'LARI
@app.route('/admin/add_task', methods=['POST'])
@login_required
def add_task():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        data = request.get_json()
        new_task = Task(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty', 'easy'),
            reward_coins=data.get('reward_coins', 10),
            energy_cost=data.get('energy_cost', 10),
            quiz_required=data.get('quiz_required', True),
            daily_reset=data.get('daily_reset', False),
            is_active=data.get('is_active', True),
            task_type=data.get('task_type', 'regular'),
            category=data.get('category', 'eco')
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Topshiriq muvaffaqiyatli qo\'shildi', 'task_id': new_task.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/get_task/<int:task_id>')
@login_required
def get_task(task_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    task = Task.query.get(task_id)
    if task:
        return jsonify({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'difficulty': task.difficulty,
                'reward_coins': task.reward_coins,
                'energy_cost': task.energy_cost,
                'quiz_required': task.quiz_required,
                'daily_reset': task.daily_reset,
                'is_active': task.is_active,
                'task_type': task.task_type,
                'category': task.category
            }
        })
    return jsonify({'success': False, 'error': 'Topshiriq topilmadi'})

@app.route('/admin/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.difficulty = data.get('difficulty', task.difficulty)
        task.reward_coins = data.get('reward_coins', task.reward_coins)
        task.energy_cost = data.get('energy_cost', task.energy_cost)
        task.quiz_required = data.get('quiz_required', task.quiz_required)
        task.daily_reset = data.get('daily_reset', task.daily_reset)
        task.is_active = data.get('is_active', task.is_active)
        task.task_type = data.get('task_type', task.task_type)
        task.category = data.get('category', task.category)
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Topshiriq muvaffaqiyatli yangilandi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    task = Task.query.get(task_id)
    if task:
        UserTask.query.filter_by(task_id=task_id).delete()
        QuizResult.query.filter_by(task_id=task_id).delete()
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Topshiriq muvaffaqiyatli o\'chirildi'})
    
    return jsonify({'success': False, 'error': 'Topshiriq topilmadi'})

@app.route('/admin/toggle_task/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    task = Task.query.get(task_id)
    if task:
        task.is_active = not task.is_active
        db.session.commit()
        status = "faol" if task.is_active else "nofaol"
        return jsonify({'success': True, 'message': f'Topshiriq {status} holatga o\'zgartirildi', 'is_active': task.is_active})
    
    return jsonify({'success': False, 'error': 'Topshiriq topilmadi'})

@app.route('/admin/generate_daily_tasks', methods=['POST'])
@login_required
def generate_daily_tasks():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        daily_task = create_daily_tasks()
        if daily_task:
            return jsonify({'success': True, 'message': 'Kunlik topshiriqlar yaratildi'})
        else:
            return jsonify({'success': False, 'error': 'Yetarli topshiriqlar mavjud emas'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/manual_daily_reset', methods=['POST'])
@login_required
def manual_daily_reset():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        daily_reset_system()
        return jsonify({'success': True, 'message': 'Kunlik yangilanish bajarildi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# YANGILIK VA E'LON FUNKSIYALARI
@app.route('/admin/add_news', methods=['POST'])
@login_required
def add_news():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        data = request.get_json()
        new_news = News(
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category', 'umumiy'),
            author_id=current_user.id,
            image_path=data.get('image_path', 'images/news_default.jpg')
        )
        db.session.add(new_news)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Yangilik muvaffaqiyatli qo\'shildi', 'news_id': new_news.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/add_announcement', methods=['POST'])
@login_required
def add_announcement():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        data = request.get_json()
        
        start_date = datetime.fromisoformat(data.get('start_date').replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data.get('end_date').replace('Z', '+00:00'))
        
        new_announcement = Announcement(
            title=data.get('title'),
            content=data.get('content'),
            announcement_type=data.get('announcement_type', 'info'),
            start_date=start_date,
            end_date=end_date,
            author_id=current_user.id
        )
        db.session.add(new_announcement)
        db.session.commit()
        return jsonify({'success': True, 'message': 'E\'lon muvaffaqiyatli qo\'shildi', 'announcement_id': new_announcement.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete_news/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    news = News.query.get(news_id)
    if news:
        db.session.delete(news)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Yangilik muvaffaqiyatli o\'chirildi'})
    
    return jsonify({'success': False, 'error': 'Yangilik topilmadi'})

@app.route('/admin/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    announcement = Announcement.query.get(announcement_id)
    if announcement:
        db.session.delete(announcement)
        db.session.commit()
        return jsonify({'success': True, 'message': 'E\'lon muvaffaqiyatli o\'chirildi'})
    
    return jsonify({'success': False, 'error': 'E\'lon topilmadi'})

@app.route('/admin/toggle_news/<int:news_id>', methods=['POST'])
@login_required
def toggle_news(news_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    news = News.query.get(news_id)
    if news:
        news.status = 'archived' if news.status == 'active' else 'active'
        db.session.commit()
        status = "faol" if news.status == 'active' else "arxiv"
        return jsonify({'success': True, 'message': f'Yangilik {status} holatga o\'zgartirildi', 'status': news.status})
    
    return jsonify({'success': False, 'error': 'Yangilik topilmadi'})

@app.route('/admin/toggle_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def toggle_announcement(announcement_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    announcement = Announcement.query.get(announcement_id)
    if announcement:
        announcement.is_active = not announcement.is_active
        db.session.commit()
        status = "faol" if announcement.is_active else "nofaol"
        return jsonify({'success': True, 'message': f'E\'lon {status} holatga o\'zgartirildi', 'is_active': announcement.is_active})
    
    return jsonify({'success': False, 'error': 'E\'lon topilmadi'})

@app.route('/admin/get_news/<int:news_id>')
@login_required
def get_news(news_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    news = News.query.get(news_id)
    if news:
        return jsonify({
            'success': True,
            'news': {
                'id': news.id,
                'title': news.title,
                'content': news.content,
                'category': news.category,
                'image_path': news.image_path,
                'status': news.status
            }
        })
    return jsonify({'success': False, 'error': 'Yangilik topilmadi'})

@app.route('/admin/get_announcement/<int:announcement_id>')
@login_required
def get_announcement(announcement_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    announcement = Announcement.query.get(announcement_id)
    if announcement:
        return jsonify({
            'success': True,
            'announcement': {
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'announcement_type': announcement.announcement_type,
                'start_date': announcement.start_date.isoformat(),
                'end_date': announcement.end_date.isoformat(),
                'is_active': announcement.is_active
            }
        })
    return jsonify({'success': False, 'error': 'E\'lon topilmadi'})

@app.route('/admin/update_news/<int:news_id>', methods=['POST'])
@login_required
def update_news(news_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        news = News.query.get_or_404(news_id)
        data = request.get_json()
        
        news.title = data.get('title', news.title)
        news.content = data.get('content', news.content)
        news.category = data.get('category', news.category)
        news.image_path = data.get('image_path', news.image_path)
        news.status = data.get('status', news.status)
        news.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Yangilik muvaffaqiyatli yangilandi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/update_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def update_announcement(announcement_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        data = request.get_json()
        
        announcement.title = data.get('title', announcement.title)
        announcement.content = data.get('content', announcement.content)
        announcement.announcement_type = data.get('announcement_type', announcement.announcement_type)
        announcement.start_date = datetime.fromisoformat(data.get('start_date').replace('Z', '+00:00'))
        announcement.end_date = datetime.fromisoformat(data.get('end_date').replace('Z', '+00:00'))
        announcement.is_active = data.get('is_active', announcement.is_active)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'E\'lon muvaffaqiyatli yangilandi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# DO'KON ADMIN FUNKSIYALARI
@app.route('/admin/add_item', methods=['POST'])
@login_required
def add_item():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        data = request.get_json()
        new_item = Item(
            name=data.get('name'),
            price=data.get('price', 0),
            item_type=data.get('item_type', 'accessory'),
            image_path=data.get('image_path', 'images/default_item.png'),
            energy_boost=data.get('energy_boost', 0),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Mahsulot muvaffaqiyatli qo\'shildi', 'item_id': new_item.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/update_item/<int:item_id>', methods=['POST'])
@login_required
def update_item(item_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        item = Item.query.get_or_404(item_id)
        data = request.get_json()
        
        item.name = data.get('name', item.name)
        item.price = data.get('price', item.price)
        item.item_type = data.get('item_type', item.item_type)
        item.image_path = data.get('image_path', item.image_path)
        item.energy_boost = data.get('energy_boost', item.energy_boost)
        item.is_active = data.get('is_active', item.is_active)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Mahsulot muvaffaqiyatli yangilandi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    item = Item.query.get(item_id)
    if item:
        Inventory.query.filter_by(item_id=item_id).delete()
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Mahsulot muvaffaqiyatli o\'chirildi'})
    
    return jsonify({'success': False, 'error': 'Mahsulot topilmadi'})

@app.route('/admin/add_energy_pack', methods=['POST'])
@login_required
def add_energy_pack():
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin huquqi yo\'q'})
    
    try:
        data = request.get_json()
        new_energy_pack = EnergyPack(
            name=data.get('name'),
            energy_amount=data.get('energy_amount', 0),
            price=data.get('price', 0),
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_energy_pack)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Energiya paketi muvaffaqiyatli qo\'shildi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# FOYDALANUVCHI ROUTE'LARI
@app.route('/games')
@login_required
def games():
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    return render_template('games.html', user=current_user, quiz_count=quiz_count)

@app.route('/news')
@login_required
def news():
    news_list = News.query.filter_by(status='active').order_by(News.created_at.desc()).all()
    now = datetime.utcnow()
    active_announcements = Announcement.query.filter(
        Announcement.start_date <= now,
        Announcement.end_date >= now,
        Announcement.is_active == True
    ).order_by(Announcement.created_at.desc()).all()
    
    return render_template('news.html', 
                         user=current_user, 
                         news_list=news_list, 
                         announcements=active_announcements)

@app.route('/news/<int:news_id>')
@login_required
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    news.views_count += 1
    db.session.commit()
    
    return render_template('news_detail.html', user=current_user, news=news)

@app.route('/leaderboard')
@login_required
def leaderboard():
    users = User.query.filter_by(role='child').order_by(User.coins.desc()).limit(20).all()
    return render_template('leaderboard.html', user=current_user, users=users)

@app.route('/missions')
@login_required
def missions():
    regular_tasks = Task.query.filter_by(task_type='regular', is_active=True).all()
    completed_tasks = UserTask.query.filter_by(user_id=current_user.id, completed=True).all()
    completed_task_ids = [ut.task_id for ut in completed_tasks]
    
    return render_template('missions.html', 
                         user=current_user, 
                         tasks=regular_tasks,
                         completed_task_ids=completed_task_ids)

@app.route('/stories')
@login_required
def stories():
    return render_template('stories.html', user=current_user)



@app.route('/profile')
@login_required
def profile():
    user_stats = {
        'total_tasks': UserTask.query.filter_by(user_id=current_user.id, completed=True).count(),
        'total_quizzes': QuizResult.query.filter_by(user_id=current_user.id).count(),
        'total_coins_earned': db.session.query(func.sum(QuizResult.coins_earned)).filter_by(user_id=current_user.id).scalar() or 0,
        'streak_days': current_user.streak
    }
    
    return render_template('profile.html', user=current_user, user_stats=user_stats)

@app.route('/posts')
@login_required
def posts():
    return render_template('posts.html', user=current_user)

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html', user=current_user)

@app.route('/dashboard_adult')
@login_required
def dashboard_adult():
    if current_user.role != 'adult':
        flash('Bu sahifa faqat kattalar uchun!', 'error')
        return redirect(url_for('dashboard'))
    return render_template('dashboard_adult.html', user=current_user)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Siz admin paneldan chiqdingiz!', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password) and user.is_admin:
            login_user(user, remember=True)
            flash('Admin panelga xush kelibsiz!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login yoki parol noto\'g\'ri!', 'error')
    
    return render_template('admin_login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Siz tizimdan chiqdingiz!', 'info')
    return redirect(url_for('login'))

# API ROUTE'LARI
@app.route('/get_user_stats')
@login_required
def get_user_stats():
    return jsonify({
        'success': True,
        'coins': current_user.coins,
        'energy': current_user.energy,
        'streak': current_user.streak,
        'level': current_user.level,
        'experience': current_user.experience
    })

@app.route('/get_daily_progress')
@login_required
def get_daily_progress():
    today = datetime.utcnow().date()
    daily_progress = DailyProgress.query.filter_by(user_id=current_user.id, date=today).first()
    
    if daily_progress:
        return jsonify({
            'success': True,
            'tasks_completed': daily_progress.tasks_completed,
            'quizzes_completed': daily_progress.quizzes_completed,
            'coins_earned': daily_progress.coins_earned
        })
    else:
        return jsonify({
            'success': True,
            'tasks_completed': 0,
            'quizzes_completed': 0,
            'coins_earned': 0
        })

if __name__ == '__main__':
    init_database()
    start_daily_scheduler()
    
    questions_data = load_questions_from_json()
    question_count = len(questions_data.get('eco_questions', []))
    print(f"📚 ML savollari yuklandi: {question_count} ta savol")
    
    print("\n🎉 EcoVerse tizimi ishga tushdi!")
    print("📍 Asosiy sahifa: http://localhost:5000")
    print("👨‍💼 Admin panel: http://localhost:5000/admin/dashboard")
    print("📰 Yangiliklar: http://localhost:5000/admin/news")
    print("📢 E'lonlar: http://localhost:5000/admin/announcements")
    print("🛍️ Do'kon boshqaruvi: http://localhost:5000/admin/shop")
    print("📅 Kunlik topshiriqlar: http://localhost:5000/admin/daily_tasks")
    print("\n🔄 Kunlik yangilanishlar soat 00:00 da avtomatik bajariladi")
    print("\n📋 Demo loginlar:")
    print("   👨‍💼 Admin: admin / admin123")
    print("   👦 Bola: eco_bola / bola123") 
    print("   👨 Katta: eco_katta / katta123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)