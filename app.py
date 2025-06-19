from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from models import db, User, Subject, Result, ResultItem, Admin
from operations import (
    register_user, login_user, logout_user, add_subject,
    get_all_subjects, declare_result, get_student_result, login_admin,
    is_result_complete
)
from utils import save_image
from xhtml2pdf import pisa
from io import BytesIO
from datetime import date
import os


# Flask App Setup
app = Flask(__name__)
app.secret_key = 'your_super_secure_key_123'

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------------- PUBLIC ----------------------

@app.route('/')
def home():
    return render_template('home.html', show_navbar=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session or 'admin' in session:
        return redirect(url_for('dashboard') if 'user' in session else url_for('admin_panel'))

    if request.method == 'POST':
        form = request.form
        image = request.files['image']
        result = register_user(form, image)
        if result['status']:
            flash(result['message'], 'success')
            return redirect(url_for('login'))
        else:
            flash(result['message'], 'danger')
    return render_template('register.html',show_navbar=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        result = login_user(request.form)
        if result['status']:
            session['user'] = result['user'].id
            return redirect(url_for('dashboard'))
        else:
            flash(result['message'], 'danger')
    return render_template('login.html', show_navbar=False)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if 'admin' in session:
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        result = login_admin(request.form)
        if result['status']:
            session['admin'] = result['admin'].id
            flash(result['message'], 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash(result['message'], 'danger')
    return render_template('admin_login.html',show_navbar=False)

# ---------------------- STUDENT ----------------------

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Login required', 'warning')
        return redirect(url_for('login'))

    user = User.get_or_none(User.id == session['user'])
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('logout'))

    subjects = get_all_subjects()
    return render_template('dashboard.html', user=user, subjects=subjects, show_navbar=True)

@app.route('/my-results')
def my_results():
    if 'user' not in session:
        return redirect(url_for('login'))

    result_data = get_student_result(session['user'])
    result = result_data['result']
    items = result_data['items']
    student = result_data['student']

    total = sum(item.marks_obtained for item in items)
    full = sum(item.total_marks for item in items)

    return render_template('results.html',
        result=result,
        result_items=items,
        student=student,
        total=total,
        full=full,
        show_navbar=False
    )

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = User.get_by_id(session['user'])

    if request.method == 'POST':
        form = request.form
        image = request.files.get('image')

        user.name = form['name']
        user.email = form['email']
        user.gender = form['gender']
        user.dob = form['dob']
        user.department = form['department']
        user.course = form['course']

        if image and image.filename:
            user.image = save_image(image)

        user.save()
        flash("Profile updated successfully", "success")
        return redirect(url_for('profile'))

    return render_template('student_profile.html', user=user, show_navbar=True)


@app.route('/download-pdf/<int:student_id>')
def download_result_pdf(student_id):
    student = User.get_or_none(User.id == student_id)
    result_data = get_student_result(student_id)

    if not result_data['result']:
        flash("Result not available!", "danger")
        return redirect(url_for('dashboard'))

    # ✅ Calculate total and full marks
    items = result_data['items']
    total = sum(item.marks_obtained for item in items)
    full = sum(item.total_marks for item in items)

    # ✅ Render HTML with total & full passed
    html = render_template('result_pdf.html',
        student=student,
        result=result_data['result'],
        result_items=items,
        total=total,
        full=full
    )

    # ✅ Convert HTML to PDF
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=result.pdf'
    return response

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

# ---------------------- ADMIN ----------------------

@app.route('/admin')
def admin_panel():
    if 'admin' not in session:
        flash("Admin login required.", "danger")
        return redirect(url_for('admin_login'))

    users = User.select()
    subjects = Subject.select()
    results = Result.select().order_by(Result.declaration_date.desc())
    return render_template('admin_panel.html', users=users, subjects=subjects, results=results, show_navbar=True)

@app.route('/admin/add-subject', methods=['GET', 'POST'])
def admin_add_subject():
    if 'admin' not in session:
        flash("Admin login required", "danger")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        result = add_subject(request.form)
        flash(result['message'], 'success' if result['status'] else 'danger')
        return redirect(url_for('admin_panel'))

    return render_template('admin_add_subject.html')

@app.route('/admin/declare-result/<int:student_id>', methods=['GET', 'POST'])
def admin_declare_result(student_id):
    if 'admin' not in session:
        flash("Admin login required", "danger")
        return redirect(url_for('admin_login'))

    student = User.get_or_none(User.id == student_id)
    if not student:
        flash("Student not found", "danger")
        return redirect(url_for('admin_panel'))

    subjects = Subject.select()
    result, _ = Result.get_or_create(student=student, declaration_date=date.today())
    existing_items = {item.subject.id: item for item in ResultItem.select().where(ResultItem.result == result)}

    edit_subject = None
    edit_marks = None
    edit_mode = False
    if request.args.get('edit'):
        edit_id = int(request.args.get('edit'))
        edit_subject = Subject.get_or_none(Subject.id == edit_id)
        edit_item = existing_items.get(edit_id)
        if edit_item:
            edit_marks = edit_item.marks_obtained
            edit_mode = True

    if request.method == 'POST':
        subject_id = int(request.form['subject_id'])
        marks = int(request.form['marks'])

        if subject_id in existing_items:
            existing_items[subject_id].marks_obtained = marks
            existing_items[subject_id].save()
            flash("Marks updated successfully!", "success")
        else:
            ResultItem.create(
                result=result,
                subject=Subject.get_by_id(subject_id),
                marks_obtained=marks,
                total_marks=100
            )
            flash("Marks saved successfully!", "success")

        return redirect(url_for('admin_declare_result', student_id=student_id))

    return render_template(
        'admin_declare_result.html',
        student=student,
        subjects=subjects,
        existing_items=existing_items,
        result=result,
        is_result_complete=is_result_complete,
        edit_subject=edit_subject,
        edit_marks=edit_marks,
        edit_mode=edit_mode
    )

@app.route('/preview-pdf/<int:student_id>')
def preview_result_pdf(student_id):
    student = User.get_or_none(User.id == student_id)
    result_data = get_student_result(student_id)

    if not result_data['result']:
        flash("Result not available!", "danger")
        return redirect(url_for('admin_panel'))

    items = result_data['items']
    total = sum(item.marks_obtained for item in items)
    full = sum(item.total_marks for item in items)

    html = render_template(
        'result_pdf.html',
        student=student,
        result=result_data['result'],
        result_items=items,
        total=total,
        full=full
    )
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)

    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=result_preview.pdf'
    return response

@app.route('/admin/finalize-result/<int:student_id>', methods=['POST'])
def finalize_result(student_id):
    if 'admin' not in session:
        flash("Admin login required", "danger")
        return redirect(url_for('admin_login'))

    flash("🎉 Final result declared successfully!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    flash("Logged out from admin panel.", "info")
    return redirect(url_for('home'))



# ---------------------- INIT ----------------------

# ✅ INIT block
if __name__ == '__main__':
    db.connect()
    db.create_tables([User, Subject, Result, ResultItem, Admin], safe=True)
    app.run(debug=True)

