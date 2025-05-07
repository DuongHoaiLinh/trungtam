from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models_db import db, Student, Class, Course, Teacher, Enrollment, ClassSchedule, User
from flask_cors import CORS
import datetime
from datetime import datetime, timedelta
import calendar
from sqlalchemy import and_, or_
import jwt
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.secret_key = 'super-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'  # Khóa bí mật cho JWT
db.init_app(app)
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500"])  # Cho phép gọi từ frontend

# Hàm tạo token JWT
def create_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=1)  # Hết hạn sau 1 ngày
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

# Hàm verify token
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Middleware kiểm tra xác thực
def authenticate(role=None):
    auth_header = request.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    user_data = None
    if token:
        user_data = verify_token(token)
    
    # Nếu không có token hoặc token không hợp lệ, kiểm tra session
    if not user_data and 'user_id' in session:
        user_data = {
            'user_id': session.get('user_id'),
            'role': session.get('role'),
            'linked_id': session.get('linked_id')
        }
    
    if not user_data:
        return None
    
    # Kiểm tra vai trò nếu được yêu cầu
    if role and user_data.get('role') != role:
        return None
    
    return user_data
@app.route("/")
def home():
    return "Hello from Flask!"

@app.route("/ping")
def ping():
    return "pong", 200
@app.route('/api/student/<int:student_id>/schedule', methods=['GET'])
def get_student_schedule(student_id):
    # Xác thực người dùng
    user_data = authenticate()
    if not user_data:
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    # Kiểm tra xem người dùng hiện tại có quyền xem lịch học của student_id không
    if user_data.get('role') != 'admin' and int(user_data.get('user_id')) != student_id:
        return jsonify({'error': 'Không có quyền xem lịch học này'}), 403
    
    # Lấy thông tin lọc từ query parameters
    course_filter = request.args.get('course')
    status_filter = request.args.get('status')
    
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    schedule_data = []

    for enrollment in enrollments:
        class_ = enrollment.class_
        course = class_.course
        teacher = class_.teacher
        
        # Áp dụng lọc theo khóa học nếu có
        if course_filter and course.name != course_filter:
            continue
            
        schedules = ClassSchedule.query.filter_by(class_id=class_.id).all()
        
        for sched in schedules:
            # Tính toán trạng thái dựa trên ngày
            today = datetime.now().date()
            start_date = class_.start_date if hasattr(class_, 'start_date') else None
            end_date = class_.end_date if hasattr(class_, 'end_date') else None
            
            if start_date and end_date:
                if today < start_date:
                    status = "Chưa bắt đầu"
                elif today > end_date:
                    status = "Đã kết thúc"
                else:
                    status = "Đang học"
            else:
                status = "Đang học"  # Mặc định nếu không có thông tin ngày
            
            # Áp dụng lọc theo trạng thái nếu có
            if status_filter and status != status_filter:
                continue
                
            schedule_item = {
                "course_name": course.name,
                "class_name": class_.name,
                "teacher_name": teacher.name,
                "schedule": f"{sched.day_of_week}, {sched.start_time.strftime('%H:%M')} - {sched.end_time.strftime('%H:%M')}",
                "from_date": class_.start_date.strftime('%d/%m/%Y') if hasattr(class_, 'start_date') and class_.start_date else "Chưa cập nhật",
                "to_date": class_.end_date.strftime('%d/%m/%Y') if hasattr(class_, 'end_date') and class_.end_date else "Chưa cập nhật",
                "status": status
            }
            schedule_data.append(schedule_item)

    return jsonify(schedule_data)

@app.route('/api/teacher/<int:teacher_id>/schedule', methods=['GET'])
def get_teacher_schedule(teacher_id):
    # Xác thực người dùng
    
    user_data = authenticate()
    
    if not user_data:
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    # Kiểm tra xem người dùng hiện tại có quyền xem lịch dạy của teacher_id không

    if user_data.get('role') != 'admin' and (user_data.get('role') != 'teacher'):
        return jsonify({'error': 'Không có quyền xem lịch dạy này'}), 403
    
    # Lấy thông tin lọc từ query parameters
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    course_filter = request.args.get('course')
    
    
    # Xử lý ngày tháng
    try:
        if date_from:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date()
            
        if date_to:
            end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            end_date = start_date + timedelta(days=6)  # Mặc định 7 ngày
    except ValueError:
        return jsonify({'error': 'Định dạng ngày không hợp lệ. Sử dụng YYYY-MM-DD'}), 400
    
    # Kiểm tra giáo viên tồn tại
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({'error': 'Không tìm thấy thông tin giáo viên'}), 404
    
    # Lấy tất cả lớp học mà giáo viên phụ trách
    teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
    
    if not teacher_classes:
        return jsonify([])  # Trả về mảng rỗng nếu không có lớp
    
    class_ids = [cls.id for cls in teacher_classes]
    
    # Lấy lịch học của các lớp
    schedules = ClassSchedule.query.filter(ClassSchedule.class_id.in_(class_ids)).all()
    
    # Tạo danh sách lịch dạy chi tiết
    teaching_schedule = []
    
    # Tạo lịch cho khoảng thời gian được yêu cầu dựa trên lịch học định kỳ
    current_date = start_date
    while current_date <= end_date:
        day_of_week = calendar.day_name[current_date.weekday()]  # Lấy tên thứ trong tuần
        
        # Tìm các lịch học vào thứ này
        for schedule in schedules:
            if schedule.day_of_week == day_of_week:
                # Lấy thông tin lớp học và khóa học
                class_info = next((cls for cls in teacher_classes if cls.id == schedule.class_id), None)
                if not class_info:
                    continue
                    
                course_info = Course.query.get(class_info.course_id)
                
                # Áp dụng lọc theo khóa học nếu có
                if course_filter and course_info.name != course_filter:
                    continue
                
                # Kiểm tra xem lớp học có trong khoảng thời gian hoạt động không
                if hasattr(class_info, 'start_date') and class_info.start_date and hasattr(class_info, 'end_date') and class_info.end_date:
                    if current_date < class_info.start_date or current_date > class_info.end_date:
                        continue
                
                # Tính toán trạng thái dựa trên ngày
                today = datetime.now().date()
                if current_date > today:
                    status = "Chưa bắt đầu"
                elif current_date.strftime('%Y-%m-%d') == today.strftime('%Y-%m-%d'):
                    status = "Đang diễn ra"
                else:
                    status = "Đã kết thúc"
                
                teaching_schedule.append({
                    'date': current_date.strftime('%d/%m/%Y'),
                    'day_of_week': day_of_week,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'class_name': class_info.name,
                    'course_name': course_info.name,
                    'room': f'P.{schedule.class_id}',  # Giả định phòng học
                    'from_date': class_info.start_date.strftime('%d/%m/%Y') if hasattr(class_info, 'start_date') and class_info.start_date else "Chưa cập nhật",
                    'to_date': class_info.end_date.strftime('%d/%m/%Y') if hasattr(class_info, 'end_date') and class_info.end_date else "Chưa cập nhật",
                    'status': status
                })
        
        current_date += timedelta(days=1)
    
    # Sắp xếp lịch dạy theo ngày và giờ
    teaching_schedule.sort(key=lambda x: (x['date'], x['start_time']))
    
    return jsonify(teaching_schedule)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    user = User.query.filter_by(email=email, password=password, role=role).first()

    if user:
        # Lưu vào session
        session['user_id'] = user.id
        session['role'] = user.role
        session['linked_id'] = user.linked_id
        
        # Tạo JWT token
        token = create_token(user.id, user.role)
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'role': user.role,
            'linked_id': user.linked_id,
            'token': token
        })
    else:
        return jsonify({'success': False, 'message': 'Sai thông tin đăng nhập'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    # Xóa session
    session.clear()
    return jsonify({'success': True, 'message': 'Đăng xuất thành công'})

@app.route('/api/verify-auth', methods=['GET'])
def verify_auth():
    user_data = authenticate()
    # return user_data
    if user_data:
        return jsonify({
            'authenticated': True,
            'user_id': user_data.get('user_id'),
            'role': user_data.get('role'),
            'linked_id': user_data.get('linked_id')  # Thêm linked_id để client có thể sử dụng
        })
    else:
        return jsonify({'authenticated': False}), 401

@app.route('/api/teachers/<int:teacher_id>', methods=['GET'])
def get_teacher(teacher_id):
    # Xác thực người dùng
    user_data = authenticate()
    if not user_data:
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    # Lấy thông tin giáo viên
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({'error': 'Không tìm thấy thông tin giáo viên'}), 404
    
    # Trả về thông tin giáo viên
    return jsonify({
        'id': teacher.id,
        'name': teacher.name, 
        'email': teacher.email if hasattr(teacher, 'email') else f"teacher{teacher.id}@polycenter.com"
    })

@app.route('/api/teacher/<int:teacher_id>/courses', methods=['GET'])
def get_teacher_courses(teacher_id):
    # Xác thực người dùng
    user_data = authenticate()
    if not user_data:
        return jsonify({'error': 'Chưa đăng nhập'}), 401
    
    # Lấy danh sách lớp học của giáo viên
    teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
    
    if not teacher_classes:
        return jsonify([])
    
    # Lấy danh sách khóa học duy nhất
    course_ids = set(cls.course_id for cls in teacher_classes)
    courses = []
    
    for course_id in course_ids:
        course = Course.query.get(course_id)
        if course:
            courses.append({
                'id': course.id,
                'name': course.name
            })
    
    return jsonify(courses)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', debug=True)
