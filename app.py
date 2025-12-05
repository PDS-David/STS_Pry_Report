from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "stss_secret_key_2025_change_this_in_production"

# Database configuration
DATABASE = 'school.db'

# Score limits - UPDATED
MAX_CA1 = 20
MAX_CA2 = 20
MAX_EXAM = 60

# School Information - UPDATED
SCHOOL_INFO = {
    'name': 'SOW THE SEED NURSERY & PRIMARY SCHOOL',
    'motto': 'Growing in wisdom and finding favour with God and Man - Lk. 2 : 52',
    'address': 'Your School Address Here',
    'phone1': '0123456789',
    'phone2': '0987654321',
    'logo': 'logo.png'  # Place your logo in static/logo.png
}

# ============ DATABASE FUNCTIONS ============

def get_db():
    """Create database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            admission_number TEXT UNIQUE,
            student_class TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Terms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            is_current BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            ca1 REAL DEFAULT 0,
            ca2 REAL DEFAULT 0,
            exam REAL DEFAULT 0,
            total REAL DEFAULT 0,
            remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (term_id) REFERENCES terms(id),
            UNIQUE(student_id, subject_id, term_id)
        )
    ''')
    
    # Users table for login
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Insert default admin user
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password) 
        VALUES ('admin', 'password123')
    ''')
    
    # Insert default term if none exists
    cursor.execute('SELECT COUNT(*) as count FROM terms')
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
            INSERT INTO terms (name, academic_year, is_current) 
            VALUES ('First Term', '2024/2025', 1)
        ''')
    
    db.commit()
    db.close()

def get_students():
    """Get all students"""
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY name').fetchall()
    db.close()
    return students

def get_classes():
    """Get list of unique classes"""
    db = get_db()
    classes = db.execute('''
        SELECT DISTINCT student_class 
        FROM students 
        ORDER BY student_class
    ''').fetchall()
    db.close()
    return [c['student_class'] for c in classes]

def get_current_term():
    """Get the current active term"""
    db = get_db()
    term = db.execute('SELECT * FROM terms WHERE is_current = 1 LIMIT 1').fetchone()
    db.close()
    return term

def get_subjects():
    """Get all subjects"""
    db = get_db()
    subjects = db.execute('SELECT * FROM subjects ORDER BY name').fetchall()
    db.close()
    return subjects

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
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        db.close()
        
        if user:
            session['username'] = username
            session['user_id'] = user['id']
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
                         session=session)

@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    """Add new student"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        admission_number = request.form.get('admission_number')
        student_class = request.form.get('student_class')
        
        try:
            db = get_db()
            db.execute(
                'INSERT INTO students (name, admission_number, student_class) VALUES (?, ?, ?)',
                (name, admission_number, student_class)
            )
            db.commit()
            db.close()
            flash(f'Student {name} added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Admission number already exists!', 'error')
    
    return render_template('add_student.html', school_info=SCHOOL_INFO)

@app.route('/student/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    
    if request.method == 'POST':
        name = request.form.get('name')
        admission_number = request.form.get('admission_number')
        student_class = request.form.get('student_class')
        
        db.execute(
            'UPDATE students SET name = ?, admission_number = ?, student_class = ? WHERE id = ?',
            (name, admission_number, student_class, student_id)
        )
        db.commit()
        db.close()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    student = db.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    db.close()
    
    return render_template('edit_student.html', student=student, school_info=SCHOOL_INFO)

@app.route('/student/delete/<int:student_id>')
def delete_student(student_id):
    """Delete student"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.execute('DELETE FROM scores WHERE student_id = ?', (student_id,))
    db.commit()
    db.close()
    
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/score_entry', methods=['GET', 'POST'])
def score_entry():
    """Score entry page"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        ca1 = float(request.form.get('ca1', 0))
        ca2 = float(request.form.get('ca2', 0))
        exam = float(request.form.get('exam', 0))
        remark = request.form.get('remark', '')
        
        # Validate scores
        if ca1 > MAX_CA1 or ca2 > MAX_CA2 or exam > MAX_EXAM:
            flash('Score exceeds maximum allowed!', 'error')
            return redirect(url_for('score_entry'))
        
        total = ca1 + ca2 + exam
        current_term = get_current_term()
        
        if not current_term:
            flash('No active term! Please create a term first.', 'error')
            return redirect(url_for('score_entry'))
        
        try:
            db = get_db()
            db.execute('''
                INSERT OR REPLACE INTO scores 
                (student_id, subject_id, term_id, ca1, ca2, exam, total, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, subject_id, current_term['id'], ca1, ca2, exam, total, remark))
            db.commit()
            db.close()
            flash('Score saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving score: {str(e)}', 'error')
    
    students = get_students()
    subjects = get_subjects()
    current_term = get_current_term()
    
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
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
    current_term = get_current_term()
    
    if not current_term:
        flash('No active term!', 'error')
        return redirect(url_for('dashboard'))
    
    # Get student scores
    scores = db.execute('''
        SELECT s.*, sub.name as subject
        FROM scores s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE s.student_id = ? AND s.term_id = ?
        ORDER BY sub.name
    ''', (student_id, current_term['id'])).fetchall()
    
    report_data = []
    total_score = 0
    
    for score in scores:
        grade = calculate_grade(score['total'])
        
        # Get class statistics
        class_scores = db.execute('''
            SELECT s.total
            FROM scores s
            JOIN students st ON s.student_id = st.id
            WHERE s.subject_id = ? AND s.term_id = ? AND st.student_class = ?
        ''', (score['subject_id'], current_term['id'], student['student_class'])).fetchall()
        
        totals = [s['total'] for s in class_scores]
        class_highest = max(totals) if totals else 0
        class_average = sum(totals) / len(totals) if totals else 0
        
        # Calculate position
        position = sum(1 for t in totals if t > score['total']) + 1
        
        report_data.append({
            'subject': score['subject'],
            'ca1': score['ca1'],
            'ca2': score['ca2'],
            'exam': score['exam'],
            'total': score['total'],
            'grade': grade,
            'position': position,
            'class_highest': class_highest,
            'class_average': f"{class_average:.1f}",
            'remark': get_remark(grade)
        })
        
        total_score += score['total']
    
    # Calculate overall statistics
    num_subjects = len(scores)
    average = total_score / num_subjects if num_subjects > 0 else 0
    
    # Get total students in class
    total_students = db.execute('''
        SELECT COUNT(DISTINCT id) as count 
        FROM students 
        WHERE student_class = ?
    ''', (student['student_class'],)).fetchone()['count']
    
    # Calculate overall position
    all_totals = db.execute('''
        SELECT st.id, SUM(s.total) as total
        FROM scores s
        JOIN students st ON s.student_id = st.id
        WHERE s.term_id = ? AND st.student_class = ?
        GROUP BY st.id
    ''', (current_term['id'], student['student_class'])).fetchall()
    
    position = sum(1 for t in all_totals if t['total'] > total_score) + 1
    
    student_stats = {
        'total': total_score,
        'average': average,
        'position': position
    }
    
    db.close()
    
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
    
    db = get_db()
    current_term = get_current_term()
    classes = get_classes()
    
    summary_data = {}
    
    for class_name in classes:
        # Get students in class
        students = db.execute('''
            SELECT * FROM students WHERE student_class = ?
        ''', (class_name,)).fetchall()
        
        # Get total scores for each student
        student_totals = []
        for student in students:
            total = db.execute('''
                SELECT SUM(total) as total
                FROM scores
                WHERE student_id = ? AND term_id = ?
            ''', (student['id'], current_term['id'])).fetchone()
            
            if total['total']:
                student_totals.append((student['name'], total['total']))
        
        # Sort and get top 3
        student_totals.sort(key=lambda x: x[1], reverse=True)
        top_students = student_totals[:3]
        
        # Calculate class average
        totals = [t[1] for t in student_totals]
        class_average = sum(totals) / len(totals) if totals else 0
        
        summary_data[class_name] = {
            'total_students': len(students),
            'class_average': class_average,
            'top_students': top_students
        }
    
    db.close()
    
    return render_template('class_summary.html',
                         summary_data=summary_data,
                         current_term=current_term)

@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    """Manage subjects"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code', '')
        
        db = get_db()
        db.execute('INSERT INTO subjects (name, code) VALUES (?, ?)', (name, code))
        db.commit()
        db.close()
        flash('Subject added successfully!', 'success')
        return redirect(url_for('subjects'))
    
    subjects = get_subjects()
    return render_template('subjects.html', subjects=subjects)

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
        is_current = 1 if request.form.get('is_current') else 0
        
        db = get_db()
        
        # If setting as current, unset all others
        if is_current:
            db.execute('UPDATE terms SET is_current = 0')
        
        db.execute(
            'INSERT INTO terms (name, academic_year, is_current) VALUES (?, ?, ?)',
            (name, academic_year, is_current)
        )
        db.commit()
        db.close()
        flash('Term added successfully!', 'success')
        return redirect(url_for('terms'))
    
    db = get_db()
    all_terms = db.execute('SELECT * FROM terms ORDER BY id DESC').fetchall()
    db.close()
    
    return render_template('terms.html', terms=all_terms)

@app.route('/manage_terms')
def manage_terms():
    """Redirect to terms"""
    return redirect(url_for('terms'))

# ============ INITIALIZE AND RUN ============

if __name__ == '__main__':
    # Initialize database on first run
    if not os.path.exists(DATABASE):
        print("Creating database...")
        init_db()
        print("Database created successfully!")
    
    print("=" * 70)
    print("SOW THE SEED NURSERY & PRIMARY SCHOOL - Management System")
    print("=" * 70)
    print("Server starting at: http://127.0.0.1:5000")
    print("Default login: admin / password123")
    print("=" * 70)
    
    app.run(debug=True)