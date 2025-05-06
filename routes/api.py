from flask import Blueprint, jsonify, current_app
from models_db import db, Student, Class, Course, Teacher, Enrollment, ClassSchedule

api = Blueprint('api', __name__)

@api.route('/courses', methods=['GET'])
def get_courses():
    # Sử dụng current_app để truy cập db
    db = current_app.extensions['sqlalchemy']
    courses = Course.query.all()
    courses_list = []
    
    for course in courses:
        classes = Class.query.filter_by(course_id=course.id).all()
        classes_list = [
            {
                'id': cls.id,
                'name': cls.name,
                'max_students': cls.max_students,
                'current_students': cls.current_students,
                'tuition_fee': cls.tuition_fee,
                'teacher': cls.teacher.name if cls.teacher else 'Chưa có giáo viên',
                'schedules': [
                    {
                        'day_of_week': schedule.day_of_week,
                        'start_time': schedule.start_time.strftime('%H:%M'),
                        'end_time': schedule.end_time.strftime('%H:%M')
                    } for schedule in ClassSchedule.query.filter_by(class_id=cls.id).all()
                ]
            } for cls in classes
        ]
        courses_list.append({
            'id': course.id,
            'name': course.name,
            'classes': classes_list
        })
    
    return jsonify(courses_list)