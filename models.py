from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    roll_no = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    year = db.Column(db.String(10))
    grade = db.Column(db.String(10))
    backlogs = db.Column(db.Integer)
    cgpa = db.Column(db.Float)

    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))


class Faculty(db.Model):
    faculty_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    branch = db.Column(db.String(50))
    salary = db.Column(db.Integer)
    performance = db.Column(db.String(50))
    specialization = db.Column(db.String(200))
    achievements = db.Column(db.Text)


class StudentMark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20))
    semester = db.Column(db.Integer)
    sub1 = db.Column(db.Integer)
    sub2 = db.Column(db.Integer)
    sub3 = db.Column(db.Integer)
    sub4 = db.Column(db.Integer)
    sub5 = db.Column(db.Integer)
    sgpa = db.Column(db.Float)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))   # who will receive
    message = db.Column(db.String(200))
    seen = db.Column(db.Boolean, default=False)