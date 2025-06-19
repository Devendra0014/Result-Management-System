from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

# ✅ Hash password
def hash_password(password):
    return generate_password_hash(password)

# ✅ Check password
def verify_password(stored_hash, provided_password):
    return check_password_hash(stored_hash, provided_password)

# ✅ Save image file with UUID filename
def save_image(image, student_name):
    ext = image.filename.rsplit('.', 1)[-1]
    safe_name = secure_filename(student_name.replace(" ", "_"))
    new_filename = f"{safe_name}_{uuid.uuid4().hex[:6]}.{ext}"

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
    image.save(filepath)
    return new_filename

# ✅ Auto-generate Roll No like STU0001
def generate_roll_no():
    from models import User
    count = User.select().count() + 1
    return f"STU{str(count).zfill(4)}"