from models import User, Subject, Result, ResultItem, Admin
from utils import save_image
from peewee import IntegrityError
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ✅ Admin Login
def login_admin(form):
    email = form['email']
    password = form['password']

    try:
        admin = Admin.get(Admin.email == email)
        if check_password_hash(admin.password, password):
            return {'status': True, 'admin': admin, 'message': 'Admin login successful'}
        else:
            return {'status': False, 'message': 'Incorrect password'}
    except Admin.DoesNotExist:
        return {'status': False, 'message': 'Admin not found'}
# ✅ Register Student
def register_user(form, image):
    email = form['email']
    if User.select().where(User.email == email).exists():
        return {'status': False, 'message': 'Email already registered'}

    # Auto-generate Roll No
    last_user = User.select().order_by(User.id.desc()).first()
    next_id = last_user.id + 1 if last_user else 1
    roll_no = f"STU{str(next_id).zfill(4)}"

    # Save image
    filename = save_image(image, form['name']) if image else None

    # ✅ Hash password
    hashed_password = generate_password_hash(form['password'])

    user = User.create(
    name=form['name'],
    email=email,
    password=hashed_password,  # ✅ store hashed password
    gender=form['gender'],
    dob=form['dob'],
    department=form['department'],
    course=form['course'],
    roll_no=roll_no,
    image=filename
    
  )

    return {'status': True, 'message': 'Registration successful! Please login.'}

# ✅ Student Login
def login_user(form):
    try:
        user = User.get(User.email == form['email'])
        if check_password_hash(user.password, form['password']):
            return {'status': True, 'user': user, 'message': 'Login successful!'}
        else:
            return {'status': False, 'message': 'Incorrect password.'}
    except User.DoesNotExist:
        return {'status': False, 'message': 'User not found.'}

# ✅ Logout
def logout_user():
    from flask import session
    session.pop('user', None)

# ✅ Add Subject
def add_subject(form):
    try:
        Subject.create(
            sub_code=form['sub_code'],
            name=form['name']
        )
        return {'status': True, 'message': 'Subject added successfully.'}
    except IntegrityError:
        return {'status': False, 'message': 'Subject code already exists.'}

# ✅ Get All Subjects
def get_all_subjects():
    return Subject.select()

# ✅ Declare Result
def declare_result(form):
    roll_no = form['roll_no']
    try:
        student = User.get(User.roll_no == roll_no)
        result = Result.create(student=student, declaration_date=datetime.date.today())
        subjects = Subject.select()
        for subject in subjects:
            key = f"marks_{subject.sub_code}"
            marks = int(form.get(key, 0))
            ResultItem.create(result=result, subject=subject, marks_obtained=marks, total_marks=100)
        return {'status': True, 'message': 'Result declared successfully!'}
    except User.DoesNotExist:
        return {'status': False, 'message': 'Student not found.'}

# ✅ Get Result for a Student
def get_student_result(user_id):
    try:
        student = User.get_by_id(user_id)
        result = Result.select().where(Result.student == student).order_by(Result.id.desc()).get()
        result_items = list(result.items)  # ✅ backref used here
        return {
            'student': student,
            'result': result,
            'items': result_items
        }
    except Result.DoesNotExist:
        return {'student': student, 'result': None, 'items': []}

# ✅ Check if all subjects have marks for a result
def is_result_complete(result):
    subjects = list(Subject.select())
    entered_subject_ids = [item.subject.id for item in result.items]
    return all(subject.id in entered_subject_ids for subject in subjects)
