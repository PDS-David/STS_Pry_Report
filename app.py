from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, UniqueConstraint
from datetime import datetime
import os
import re

app = Flask(__name__)

# =================================================================
# 🔒 CRITICAL DATABASE CONFIGURATION
# =================================================================

# Check if we want to use PostgreSQL or SQLite
USE_LOCAL_DB = os.environ.get("USE_LOCAL_DB", "true").lower() == "true"

if USE_LOCAL_DB:
    # Force local SQLite database
    database_url = "sqlite:///school.db"
    print("🔵 Using LOCAL SQLite database: school.db")
else:
    # Use DATABASE_URL from environment (for production)
    database_url = os.environ.get("DATABASE_URL", "sqlite:///school.db")
    
    # Render-specific fix: SQLAlchemy expects 'postgresql://' but Render provides 'postgres://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"🟢 Using REMOTE database: {database_url[:30]}...")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url

# Use os.environ.get for SECRET_KEY as well (BEST PRACTICE)
app.config['SECRET_KEY'] = os.environ.get(
    "SECRET_KEY",
    "stss_secret_key_2025_change_this_in_production"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Score limits - UPDATED
MAX_CA1 = 20
MAX_CA2 = 20
MAX_EXAM = 60

# School Information - UPDATED
SCHOOL_INFO = {
    'name': 'SOW THE SEED NURSERY & PRIMARY SCHOOL',
    'motto': 'Growing in wisdom and finding favour with God and Man - Lk. 2 : 52',
    'address': 'Olosan Road, Alakia, Ibadan',
    'phone1': '08033269042',
    'phone2': '08138044735',
    'logo': 'logo.png'  # Place your logo in static/logo.png
}

# ============ DATABASE MODELS (SQLAlchemy) ============

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    admission_number = db.Column(db.Text, unique=True)
    student_class = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    scores = db.relationship('Score', backref='student', lazy=True, cascade="all, delete-orphan")

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    code = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    scores = db.relationship('Score', backref='subject', lazy=True, cascade="all, delete-orphan")

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    academic_year = db.Column(db.Text, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    scores = db.relationship('Score', backref='term', lazy=True, cascade="all, delete-orphan")

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    ca1 = db.Column(db.Float, default=0)
    ca2 = db.Column(db.Float, default=0)
    exam = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'term_id', name='_student_subject_term_uc'),
    )

# ============ DATABASE UTILITY FUNCTIONS ============

def init_db():
    """Initialize database with tables and default data (SQLAlchemy)"""
    try:
        # Create all tables defined by the models
        db.create_all()

        # Insert default admin user
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123'))
            db.session.commit()
            print("✅ Default admin user created")

        # Insert default term if none exists
        if not Term.query.first():
            db.session.add(Term(name='First Term', academic_year='2024/2025', is_current=True))
            db.session.commit()
            print("✅ Default term created")
            
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        db.session.rollback()

def get_students():
    """Get all students"""
    return Student.query.order_by(Student.name).all()

def get_classes():
    """Get list of unique classes"""
    # Use SQLAlchemy's distinct function
    return [c[0] for c in db.session.query(Student.student_class).distinct().order_by(Student.student_class).all()]

def get_current_term():
    """Get the current active term"""
    return Term.query.filter_by(is_current=True).first()

def get_subjects():
    """Get all subjects"""
    return Subject.query.order_by(Subject.name).all()

def calculate_grade(total):
    """Calculate grade based on total score"""
    if total >= 70:
        return 'A'
    elif total >= 60:
        return 'B'
    elif total >= 50:
        return 'C'
    elif total >= 40:
        return 'D'
    elif total >= 30:
        return 'E'
    else:
        return 'F'

def get_remark(grade):
    """Get remark based on grade"""
    remarks = {
        'A': 'Excellent',
        'B': 'Very Good',
        'C': 'Good',
        'D': 'Fair',
        'E': 'Poor',
        'F': 'Fail'
    }
    return remarks.get(grade, '')

# ============ ROUTES ============

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Use SQLAlchemy ORM to check credentials
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['username'] = username
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html', school_info=SCHOOL_INFO)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    students = get_students()
    classes = get_classes()
    current_term = get_current_term()
    
    return render_template('dashboard.html', 
                         students=students, 
                         classes=classes, 
                         current_term=current_term,
                         session=session,
                         school_info=SCHOOL_INFO)

@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    """Add new student"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        admission_number = request.form.get('admission_number')
        student_class = request.form.get('student_class')
        
        new_student = Student(name=name, admission_number=admission_number, student_class=student_class)
        db.session.add(new_student)
        
        try:
            db.session.commit()
            flash(f'Student {name} added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception:
            db.session.rollback()
            flash('Admission number already exists! Please use a unique number.', 'error')
    
    return render_template('add_student.html', school_info=SCHOOL_INFO)

@app.route('/student/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.admission_number = request.form.get('admission_number')
        student.student_class = request.form.get('student_class')
        
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_student.html', student=student, school_info=SCHOOL_INFO)

@app.route('/student/delete/<int:student_id>')
def delete_student(student_id):
    """Delete student"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    student = Student.query.get_or_404(student_id)
    
    # SQLAlchemy cascades delete to scores automatically (due to 'cascade="all, delete-orphan"' in model)
    db.session.delete(student)
    db.session.commit()
    
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/score_entry', methods=['GET', 'POST'])
def score_entry():
    """Score entry page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    students = get_students()
    subjects = get_subjects()
    current_term = get_current_term()

    if not current_term:
        flash('No active term! Please create a term first.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            student_id = int(request.form.get('student_id'))
            subject_id = int(request.form.get('subject_id'))
            ca1 = float(request.form.get('ca1', 0))
            ca2 = float(request.form.get('ca2', 0))
            exam = float(request.form.get('exam', 0))
            remark = request.form.get('remark', '')
            
            # Validate scores
            if ca1 > MAX_CA1 or ca2 > MAX_CA2 or exam > MAX_EXAM:
                flash('Score exceeds maximum allowed!', 'error')
                return redirect(url_for('score_entry'))
            
            total = ca1 + ca2 + exam
            
            # Check if score exists (for INSERT OR REPLACE logic)
            score_record = Score.query.filter_by(
                student_id=student_id, 
                subject_id=subject_id, 
                term_id=current_term.id
            ).first()
            
            if score_record:
                # Update existing record
                score_record.ca1 = ca1
                score_record.ca2 = ca2
                score_record.exam = exam
                score_record.total = total
                score_record.remark = remark
            else:
                # Create new record
                new_score = Score(
                    student_id=student_id, 
                    subject_id=subject_id, 
                    term_id=current_term.id,
                    ca1=ca1, ca2=ca2, exam=exam, total=total, remark=remark
                )
                db.session.add(new_score)
                
            db.session.commit()
            flash('Score saved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving score: {str(e)}', 'error')
            
    return render_template('score_entry.html',
                         students=students,
                         subjects=subjects,
                         current_term=current_term,
                         school_info=SCHOOL_INFO,
                         MAX_CA1=MAX_CA1,
                         MAX_CA2=MAX_CA2,
                         MAX_EXAM=MAX_EXAM)

@app.route('/student/report/<int:student_id>')
def student_report(student_id):
    """Generate student report card"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    student = Student.query.get_or_404(student_id)
    current_term = get_current_term()
    
    if not current_term:
        flash('No active term!', 'error')
        return redirect(url_for('dashboard'))
    
    # Get student scores and subject name (using ORM JOIN)
    scores_query = db.session.query(
        Score, 
        Subject.name.label('subject_name')
    ).join(Subject).filter(
        Score.student_id == student_id, 
        Score.term_id == current_term.id
    ).order_by(Subject.name).all()
    
    report_data = []
    total_score = 0
    
    # Step 1: Pre-fetch all class totals for position calculation efficiency
    class_totals_query = db.session.query(
        Student.id, 
        func.sum(Score.total).label('total')
    ).join(Score).filter(
        Student.student_class == student.student_class,
        Score.term_id == current_term.id
    ).group_by(Student.id).all()
    
    all_student_totals = {row.id: row.total for row in class_totals_query}
    
    # Step 2: Iterate through scores to build report data
    for score_obj, subject_name in scores_query:
        total_score += score_obj.total
        grade = calculate_grade(score_obj.total)
        
        # Get class statistics for the SPECIFIC SUBJECT
        class_scores_for_subject = db.session.query(Score.total).join(Student).filter(
            Score.subject_id == score_obj.subject_id, 
            Score.term_id == current_term.id, 
            Student.student_class == student.student_class
        ).all()
        
        totals = [s[0] for s in class_scores_for_subject]
        class_highest = max(totals) if totals else 0
        class_average = sum(totals) / len(totals) if totals else 0
        
        # Calculate subject position
        subject_position = sum(1 for t in totals if t > score_obj.total) + 1
        
        report_data.append({
            'subject': subject_name,
            'ca1': score_obj.ca1,
            'ca2': score_obj.ca2,
            'exam': score_obj.exam,
            'total': score_obj.total,
            'grade': grade,
            'position': subject_position,
            'class_highest': class_highest,
            'class_average': f"{class_average:.1f}",
            'remark': get_remark(grade)
        })
    
    # Step 3: Calculate overall statistics
    num_subjects = len(scores_query)
    average = total_score / num_subjects if num_subjects > 0 else 0
    
    # Get total students in class
    total_students = Student.query.filter_by(student_class=student.student_class).count()
    
    # Calculate overall position
    student_total_score = all_student_totals.get(student.id, 0)
    overall_position = sum(1 for total in all_student_totals.values() if total > student_total_score) + 1

    student_stats = {
        'total': total_score,
        'average': average,
        'position': overall_position
    }
    
    return render_template('report.html',
                         student=student,
                         report_data=report_data,
                         student_stats=student_stats,
                         total_students=total_students,
                         current_term=current_term,
                         school_info=SCHOOL_INFO)

@app.route('/class_summary')
def class_summary():
    """Class summary report"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_term = get_current_term()
    classes = get_classes()
    summary_data = {}
    
    if not current_term:
        flash('No active term!', 'error')
        return redirect(url_for('dashboard'))

    for class_name in classes:
        students_in_class = Student.query.filter_by(student_class=class_name).all()
        total_students = len(students_in_class)

        student_totals_query = db.session.query(
            Student.name, 
            func.sum(Score.total).label('total')
        ).join(Score).filter(
            Student.student_class == class_name,
            Score.term_id == current_term.id
        ).group_by(Student.name).all()
        
        student_totals = [(row.name, row.total) for row in student_totals_query if row.total is not None]
        student_totals.sort(key=lambda x: x[1], reverse=True)
        top_students = student_totals[:3]
        
        totals = [t[1] for t in student_totals]
        class_average = sum(totals) / len(totals) if totals else 0
        
        summary_data[class_name] = {
            'total_students': total_students,
            'class_average': class_average,
            'top_students': top_students
        }
    
    return render_template('class_summary.html',
                         summary_data=summary_data,
                         current_term=current_term,
                         school_info=SCHOOL_INFO)

@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    """Manage subjects"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code', '')
        
        new_subject = Subject(name=name, code=code)
        db.session.add(new_subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
        return redirect(url_for('subjects'))
    
    subjects = get_subjects()
    return render_template('subjects.html', subjects=subjects, school_info=SCHOOL_INFO)

@app.route('/manage_subjects')
def manage_subjects():
    """Redirect to subjects"""
    return redirect(url_for('subjects'))

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    """Manage terms"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        academic_year = request.form.get('academic_year')
        is_current = request.form.get('is_current') == 'on'
        
        # If setting as current, unset all others
        if is_current:
            Term.query.update({Term.is_current: False})
        
        new_term = Term(name=name, academic_year=academic_year, is_current=is_current)
        db.session.add(new_term)
        db.session.commit()
        
        flash('Term added successfully!', 'success')
        return redirect(url_for('terms'))
    
    all_terms = Term.query.order_by(Term.id.desc()).all()
    
    return render_template('terms.html', terms=all_terms, school_info=SCHOOL_INFO)

@app.route('/manage_terms')
def manage_terms():
    """Redirect to terms"""
    return redirect(url_for('terms'))

# ============ INITIALIZE AND RUN ============

with app.app_context():
    try:
        # Try to query the database to check connectivity
        db.session.query(User).first()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Database not initialized, creating tables... Error: {e}")
        # If anything goes wrong (no tables), create them and seed minimum data
        init_db()

if __name__ == '__main__':
    # Local dev only
    app.run(debug=True, host='0.0.0.0', port=5000)