from peewee import *
import os

# SQLite database path
db = SqliteDatabase(os.path.join(os.path.dirname(__file__), 'database.db'))

# ✅ Base Model
class BaseModel(Model):
    class Meta:
        database = db

# ✅ Admin Model
class Admin(BaseModel):
    email = CharField(unique=True)
    password = CharField()


# ✅ User Model
class User(BaseModel):
    name = CharField()
    email = CharField(unique=True)
    roll_no = CharField(unique=True)
    image = CharField(null=True)
    password = CharField()
    dob = DateField(null=True)
    gender = CharField(null=True)
    department = CharField(null=True)
    course = CharField(null=True)


# ✅ Subject Model
class Subject(BaseModel):
    sub_code = CharField(unique=True)
    name = CharField()

# ✅ Result Model
class Result(BaseModel):
    student = ForeignKeyField(User, backref='results')
    declaration_date = DateField()

# ✅ ResultItem Model (1 result has many subject marks)
class ResultItem(BaseModel):
    result = ForeignKeyField(Result, backref='items')
    subject = ForeignKeyField(Subject)
    marks_obtained = IntegerField()
    total_marks = IntegerField()
