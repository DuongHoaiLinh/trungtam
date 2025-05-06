from app import app, db
from models_db import User, Student, Teacher, Course, Class, Enrollment, Attendance, AbsenceRequest, ClassSchedule, TestResult, TeacherSalary

from faker import Faker
import random
from datetime import datetime, time, date

fake = Faker()

def reset_database():
    db.drop_all()
    db.create_all()
    print("✅ Database reset thành công.")

def seed_data():
    # === GIÁO VIÊN ===
    teachers = []
    for _ in range(5):
        t = Teacher(
            name=fake.name(),
            image_url=fake.image_url(),
            age=random.randint(28, 60),
            specialization=fake.job(),
            qualification=fake.word(),
            bio=fake.text(),
            phone=fake.phone_number(),
            email=fake.unique.email()
        )
        db.session.add(t)
        teachers.append(t)

    # === HỌC VIÊN ===
    students = []
    for _ in range(20):
        s = Student(
            name=fake.name(),
            phone=fake.phone_number(),
            email=fake.unique.email()
        )
        db.session.add(s)
        students.append(s)

    # === KHÓA HỌC ===
    courses = []
    for name in ["Toán", "Lý", "Hóa", "Văn", "Anh"]:
        c = Course(name=name)
        db.session.add(c)
        courses.append(c)

    db.session.commit()

    # === LỚP HỌC ===
    classes = []
    for _ in range(6):
        c = Class(
            course_id=random.choice(courses).id,
            name=f"Lớp {fake.word()}",
            max_students=30,
            teacher_id=random.choice(teachers).id,
            tuition_fee=random.randint(1000000, 3000000),
            current_students=0
        )
        db.session.add(c)
        classes.append(c)
    db.session.commit()

    # === ENROLLMENTS ===
    for s in students:
        selected_classes = random.sample(classes, k=random.randint(1, 3))
        for c in selected_classes:
            db.session.add(Enrollment(student_id=s.id, class_id=c.id))
            c.current_students += 1
    db.session.commit()

    # === USERS ===
    for s in students:
        db.session.add(User(role='student', email=s.email, password='123456', linked_id=s.id))
    for t in teachers:
        db.session.add(User(role='teacher', email=t.email, password='123456', linked_id=t.id))
    db.session.add(User(role='admin', email='admin@center.com', password='admin123', linked_id=0))
    db.session.commit()

    # === LỊCH HỌC ===
    for c in classes:
        for day in ['Monday', 'Wednesday']:
            db.session.add(ClassSchedule(
                class_id=c.id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(10, 0)
            ))

    # === ĐIỂM DANH & KẾT QUẢ ===
    for s in students:
        for c in classes:
            db.session.add(Attendance(
                class_id=c.id,
                student_id=s.id,
                date=date.today(),
                time=time(8, 0),
                absent=random.choice([False, True])
            ))
            db.session.add(TestResult(
                student_id=s.id,
                course_id=c.course_id,
                score=round(random.uniform(5, 10), 2)
            ))

    # === LƯƠNG GIÁO VIÊN ===
    for t in teachers:
        sessions = random.randint(5, 15)
        db.session.add(TeacherSalary(
            teacher_id=t.id,
            month='2025-05',
            total_sessions=sessions,
            salary_per_session=500000,
            total_salary=sessions * 500000
        ))

    db.session.commit()
    print("✅ Đã tạo dữ liệu mẫu thành công.")

if __name__ == "__main__":
    with app.app_context():
        reset_database()
        seed_data()
