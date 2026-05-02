from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///taskmanager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to continue.'

# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

project_members = db.Table('project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin or member
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks_assigned = db.relationship('Task', backref='assignee', lazy=True)

    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('User', secondary=project_members, backref='projects')
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default='todo')  # todo, in_progress, done
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < date.today() and self.status != 'done'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'member')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome, {name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        all_tasks = Task.query.all()
        projects = Project.query.all()
    else:
        all_tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        projects = current_user.projects

    todo = sum(1 for t in all_tasks if t.status == 'todo')
    in_progress = sum(1 for t in all_tasks if t.status == 'in_progress')
    done = sum(1 for t in all_tasks if t.status == 'done')
    overdue = sum(1 for t in all_tasks if t.is_overdue)

    recent_tasks = sorted(all_tasks, key=lambda t: t.created_at, reverse=True)[:5]

    return render_template('dashboard.html',
        todo=todo, in_progress=in_progress, done=done, overdue=overdue,
        recent_tasks=recent_tasks, projects=projects, total=len(all_tasks)
    )

# ─────────────────────────────────────────
# PROJECTS
# ─────────────────────────────────────────

@app.route('/projects')
@login_required
def projects():
    if current_user.role == 'admin':
        all_projects = Project.query.all()
    else:
        all_projects = current_user.projects
    all_users = User.query.all()
    return render_template('projects.html', projects=all_projects, users=all_users)

@app.route('/projects/create', methods=['POST'])
@login_required
def create_project():
    if current_user.role != 'admin':
        flash('Only admins can create projects.', 'error')
        return redirect(url_for('projects'))

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    member_ids = request.form.getlist('members')

    if not name:
        flash('Project name is required.', 'error')
        return redirect(url_for('projects'))

    project = Project(name=name, description=description, created_by=current_user.id)
    for mid in member_ids:
        user = User.query.get(int(mid))
        if user:
            project.members.append(user)
    db.session.add(project)
    db.session.commit()
    flash('Project created!', 'success')
    return redirect(url_for('projects'))

@app.route('/projects/<int:pid>/delete', methods=['POST'])
@login_required
def delete_project(pid):
    if current_user.role != 'admin':
        flash('Unauthorized.', 'error')
        return redirect(url_for('projects'))
    project = Project.query.get_or_404(pid)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'success')
    return redirect(url_for('projects'))

# ─────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────

@app.route('/tasks')
@login_required
def tasks():
    if current_user.role == 'admin':
        all_tasks = Task.query.order_by(Task.created_at.desc()).all()
        all_projects = Project.query.all()
    else:
        all_tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.created_at.desc()).all()
        all_projects = current_user.projects

    all_users = User.query.all()
    return render_template('tasks.html', tasks=all_tasks, projects=all_projects, users=all_users)

@app.route('/tasks/create', methods=['POST'])
@login_required
def create_task():
    if current_user.role != 'admin':
        flash('Only admins can create tasks.', 'error')
        return redirect(url_for('tasks'))

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    project_id = request.form.get('project_id')
    assigned_to = request.form.get('assigned_to')
    priority = request.form.get('priority', 'medium')
    due_date_str = request.form.get('due_date')

    if not title or not project_id:
        flash('Title and project are required.', 'error')
        return redirect(url_for('tasks'))

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    task = Task(
        title=title,
        description=description,
        project_id=int(project_id),
        assigned_to=int(assigned_to) if assigned_to else None,
        priority=priority,
        due_date=due_date
    )
    db.session.add(task)
    db.session.commit()
    flash('Task created!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:tid>/status', methods=['POST'])
@login_required
def update_task_status(tid):
    task = Task.query.get_or_404(tid)

    # Admin can update any task, member can only update their own
    if current_user.role != 'admin' and task.assigned_to != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('tasks'))

    new_status = request.form.get('status')
    if new_status in ['todo', 'in_progress', 'done']:
        task.status = new_status
        db.session.commit()
        flash('Task status updated!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:tid>/delete', methods=['POST'])
@login_required
def delete_task(tid):
    if current_user.role != 'admin':
        flash('Only admins can delete tasks.', 'error')
        return redirect(url_for('tasks'))
    task = Task.query.get_or_404(tid)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('tasks'))

# ─────────────────────────────────────────
# API (for JS fetch calls)
# ─────────────────────────────────────────

@app.route('/api/projects/<int:pid>/members')
@login_required
def project_members_api(pid):
    project = Project.query.get_or_404(pid)
    return jsonify([{'id': u.id, 'name': u.name} for u in project.members])

# ─────────────────────────────────────────
# INIT
# ─────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
