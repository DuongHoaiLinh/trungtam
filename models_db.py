from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time, date

# Khởi tạo SQLAlchemy
db = SQLAlchemy()

# === BẢNG USER ===
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student, guest
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    linked_id = db.Column(db.Integer, nullable=False)  # liên kết với student_id, teacher_id nếu cần

# === BẢNG HỌC VIÊN ===
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# === BẢNG GIÁO VIÊN ===
class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255))
    age = db.Column(db.Integer)
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    bio = db.Column(db.Text)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# === BẢNG KHÓA HỌC ===
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# === BẢNG LỚP HỌC ===
class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    max_students = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    tuition_fee = db.Column(db.Float, nullable=False)
    current_students = db.Column(db.Integer, default=0)

    course = db.relationship('Course', backref='classes')
    teacher = db.relationship('Teacher', backref='classes')

# === LIÊN KẾT HỌC VIÊN - LỚP HỌC ===
class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)

    student = db.relationship('Student', backref='enrollments')
    class_ = db.relationship('Class', backref='enrollments')

# === BẢNG ĐIỂM DANH ===
class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    absent = db.Column(db.Boolean, default=False)

# === BẢNG XIN PHÉP NGHỈ ===
class AbsenceRequest(db.Model):
    __tablename__ = 'absence_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    schedule_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('teachers.id'))  # hoặc admin ID nếu cần
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

# === BẢNG LỊCH HỌC LỚP HỌC ===
class ClassSchedule(db.Model):
    __tablename__ = 'class_schedules'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # e.g., Monday, Tuesday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

# === BẢNG KẾT QUẢ KIỂM TRA ===
class TestResult(db.Model):
    __tablename__ = 'test_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    test_date = db.Column(db.Date, default=date.today)

    student = db.relationship('Student', backref='test_results')
    course = db.relationship('Course', backref='test_results')

# === BẢNG LƯƠNG GIÁO VIÊN ===
class TeacherSalary(db.Model):
    __tablename__ = 'teacher_salaries'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # format: YYYY-MM
    total_sessions = db.Column(db.Integer, default=0)
    salary_per_session = db.Column(db.Float, nullable=False)
    total_salary = db.Column(db.Float, nullable=False)

    teacher = db.relationship('Teacher', backref='salaries')
