from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "replace_this_with_a_random_secret"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "students.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.String(20), nullable=True)  # store as string for simplicity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Student {self.roll_no} | {self.name}>"

# Create DB if it doesn't exist
@app.before_first_request
def create_tables():
    db.create_all()

# --- Routes ---
@app.route('/')
def home():
    total = Student.query.count()
    latest = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    return render_template('index.html', total=total, latest=latest)

@app.route('/students')
def list_students():
    q = request.args.get('q', '').strip()
    if q:
        # simple search across name, roll_no, email, department
        entries = Student.query.filter(
            (Student.name.ilike(f"%{q}%")) |
            (Student.roll_no.ilike(f"%{q}%")) |
            (Student.email.ilike(f"%{q}%")) |
            (Student.department.ilike(f"%{q}%"))
        ).order_by(Student.id.desc()).all()
    else:
        entries = Student.query.order_by(Student.id.desc()).all()
    return render_template('list.html', students=entries, q=q)

@app.route('/student/add', methods=['GET','POST'])
def add_student():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no').strip()
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        department = request.form.get('department').strip()
        dob = request.form.get('dob').strip()
        if not roll_no or not name:
            flash("Roll number and Name are required.", "danger")
            return redirect(url_for('add_student'))
        # prevent duplicate roll numbers
        existing = Student.query.filter_by(roll_no=roll_no).first()
        if existing:
            flash("A student with that roll number already exists.", "danger")
            return redirect(url_for('add_student'))
        student = Student(roll_no=roll_no, name=name, email=email, department=department, dob=dob)
        db.session.add(student)
        db.session.commit()
        flash("Student added successfully.", "success")
        return redirect(url_for('list_students'))
    return render_template('add_edit.html', action="Add", student=None)

@app.route('/student/edit/<int:id>', methods=['GET','POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        roll_no = request.form.get('roll_no').strip()
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        department = request.form.get('department').strip()
        dob = request.form.get('dob').strip()
        if not roll_no or not name:
            flash("Roll number and Name are required.", "danger")
            return redirect(url_for('edit_student', id=id))
        # check duplicate roll_no if changed
        other = Student.query.filter(Student.roll_no==roll_no, Student.id!=id).first()
        if other:
            flash("Another student already uses that roll number.", "danger")
            return redirect(url_for('edit_student', id=id))
        student.roll_no = roll_no
        student.name = name
        student.email = email
        student.department = department
        student.dob = dob
        db.session.commit()
        flash("Student updated successfully.", "success")
        return redirect(url_for('list_students'))
    return render_template('add_edit.html', action="Edit", student=student)

@app.route('/student/delete/<int:id>', methods=['POST'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted.", "warning")
    return redirect(url_for('list_students'))

# small API to fetch student data (optional)
@app.route('/api/student/<int:id>')
def api_student(id):
    student = Student.query.get_or_404(id)
    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "email": student.email,
        "department": student.department,
        "dob": student.dob
    }

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)