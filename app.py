from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pandas as pd
from utils import send_email_reminder
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courtesy_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------------- MODELS ----------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150))
    last_contact_date = db.Column(db.Date)
    color = db.Column(db.String(20))
    updated_by = db.Column(db.String(100))
    last_updated = db.Column(db.DateTime)
    history = db.Column(db.Text)

# ---------------------- LOGIN ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------------- DASHBOARD ----------------------
@app.route('/dashboard')
@login_required
def dashboard():
    clients = Client.query.all()
    return render_template('dashboard.html', clients=clients)

# ---------------------- ADD / UPDATE CLIENT ----------------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        new_date = datetime.strptime(request.form['last_contact_date'], '%Y-%m-%d')
        color = request.form['color']
        old_date = client.last_contact_date.strftime('%Y-%m-%d') if client.last_contact_date else 'N/A'

        client.last_contact_date = new_date
        client.color = color
        client.updated_by = current_user.username
        client.last_updated = datetime.now()
        client.history = (client.history or '') + f"\n[{datetime.now()}] {current_user.username} changed contact date from {old_date} to {new_date.strftime('%Y-%m-%d')}"

        db.session.commit()
        flash('Client updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_client.html', client=client)

# ---------------------- AUTO REMINDER ----------------------
def check_reminders():
    clients = Client.query.all()
    for client in clients:
        if client.last_contact_date:
            days_since = (datetime.now().date() - client.last_contact_date).days
            if days_since >= 90:
                send_email_reminder(client.company_name, client.last_contact_date, days_since)

# Scheduler runs daily
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', days=1)
scheduler.start()

# ---------------------- INITIALIZE ----------------------
def init_db():
    if not os.path.exists('courtesy_tracker.db'):
        db.create_all()
        df = pd.read_excel('data/clients.xlsx')
        for _, row in df.iterrows():
            client = Client(
                company_name=row['COMPANY NAME'],
                last_contact_date=pd.to_datetime(row['LAST CONTACT DATE'], errors='coerce'),
                color='',
                updated_by='System',
                last_updated=datetime.now(),
                history='Imported from Excel'
            )
            db.session.add(client)
        db.session.commit()
        print("Database initialized with Excel data.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
