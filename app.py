from flask import Flask, render_template, request, redirect, session
from models import db, Student, Faculty, User, StudentMark
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os
from models import Notification
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db.init_app(app)
def create_notification(username, message):
    db.session.add(Notification(
        username=username,
        message=message,
        seen=False
    ))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="HIMESH").first():
        db.session.add(User(
            username="HIMESH",
            password=generate_password_hash("HIMESH123"),
            role="admin"
        ))
        db.session.commit()


# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        r = request.form["role"]

        user = User.query.filter_by(username=u, role=r).first()

        if user and check_password_hash(user.password, p):
            session["user"] = u
            session["role"] = r

            if r == "admin":
                return redirect("/admin")
            elif r == "faculty":
                return redirect("/faculty")
            else:
                return redirect("/student")

    return render_template("login.html")


# ---------- ADMIN ----------
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")

    students = Student.query.all()
    faculty = Faculty.query.all()

    toppers = sorted(students, key=lambda x: (x.cgpa or 0), reverse=True)

    return render_template("admin_dashboard.html",
                           students=students,
                           faculty=faculty,
                           toppers=toppers[:5])


# ---------- FACULTY ----------
@app.route("/faculty")
def faculty_dashboard():
    fid = session["user"]
    faculty = Faculty.query.get(fid)

    students = Student.query.all()
    notifications = Notification.query.filter_by(username=fid).all()

    subject = faculty.specialization   # example: sub1

    student_marks = []

    for s in students:
        marks = StudentMark.query.filter_by(roll_no=s.roll_no).all()

        for m in marks:
            student_marks.append({
                "roll_no": s.roll_no,
                "name": s.name,
                "semester": m.semester,
                "mark": getattr(m, subject)  # dynamic column access
            })

    return render_template("faculty_dashboard.html",
                           students=students,
                           notifications=notifications,
                           subject=subject,
                           student_marks=student_marks)

@app.route("/faculty_profile")
def faculty_profile():
    fid = session["user"]
    faculty = Faculty.query.get(fid)
    return render_template("faculty_profile.html", faculty=faculty)


# ---------- STUDENT ----------
@app.route("/student")
def student_dashboard():
    roll = session["user"]
    student = Student.query.get(roll)
    marks = StudentMark.query.filter_by(roll_no=roll).all()
    notifications = Notification.query.filter_by(username=roll).all()
    return render_template("student_dashboard.html", student=student, marks=marks, notifications=notifications)


@app.route("/student_profile")
def student_profile():
    roll = session["user"]
    student = Student.query.get(roll)
    marks = StudentMark.query.filter_by(roll_no=roll).all()
    return render_template("student_profile.html", student=student, marks=marks)


# ---------- ADD STUDENT ----------
@app.route("/add_student", methods=["POST"])
def add_student():
    roll = request.form["roll_no"]

    db.session.add(Student(
        roll_no=roll,
        name=request.form["name"],
        year=request.form["year"],
        grade=request.form["grade"],
        backlogs=int(request.form["backlogs"]),
        cgpa=0,
        email=request.form["email"],
        phone=request.form["phone"]
    ))

    db.session.add(User(
        username=roll,
        password=generate_password_hash("1234"),
        role="student"
    ))
    create_notification(roll, "Your student account has been created.") 

    db.session.commit()
    return redirect("/admin")


# ---------- ADD FACULTY ----------
@app.route("/add_faculty", methods=["POST"])
def add_faculty():
    fid = request.form["faculty_id"]

    db.session.add(Faculty(
        faculty_id=fid,
        name=request.form["name"],
        branch=request.form["branch"],
        salary=int(request.form["salary"]),
        performance=request.form["performance"],
        specialization=request.form["specialization"],
        achievements=request.form["achievements"]
    ))

    db.session.add(User(
        username=fid,
        password=generate_password_hash("1234"),
        role="faculty"
    ))
    create_notification(fid, "Faculty account created by admin.")

    db.session.commit()
    return redirect("/admin")


# ---------- UPLOAD MARKS ----------
@app.route("/upload_marks", methods=["POST"])
def upload_marks():
    file = request.files["file"]
    semester = int(request.form["semester"])

    if file:
        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(path)

        df = pd.read_excel(path)
        df.columns = df.columns.str.strip().str.lower()
        df["roll_no"] = df["roll_no"].astype(str).str.strip().str.upper()

        for _, row in df.iterrows():
            roll = row["roll_no"]

            marks = [row["sub1"], row["sub2"], row["sub3"], row["sub4"], row["sub5"]]
            sgpa = round((sum(marks)/5)/9.5, 2)
            create_notification(roll, f"Semester {semester} marks uploaded. SGPA calculated.")

            db.session.add(StudentMark(
                roll_no=roll,
                semester=semester,
                sub1=float(row["sub1"]),
                sub2=float(row["sub2"]),
                sub3=float(row["sub3"]),
                sub4=float(row["sub4"]),
                sub5=float(row["sub5"]),
                sgpa=sgpa
            ))

        # update cgpa
        students = Student.query.all()
        for s in students:
            sems = StudentMark.query.filter_by(roll_no=s.roll_no).all()
            
            if sems:
                s.cgpa = round(sum([x.sgpa for x in sems])/len(sems),2)
            create_notification(s.roll_no, f"Your CGPA updated to {s.cgpa}")

        db.session.commit()

    return redirect("/admin")
# ---------- UPLOAD STUDENTS ----------
@app.route("/upload_students", methods=["POST"])
def upload_students():
    file = request.files["file"]

    if file:
        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(path)

        df = pd.read_excel(path)

        # clean column names
        df.columns = df.columns.str.strip().str.lower()

        for _, row in df.iterrows():
            roll = str(row["roll_no"]).strip().upper()

            # add student
            db.session.add(Student(
                roll_no=roll,
                name=row["name"],
                year=row["year"],
                grade=row["grade"],
                backlogs=int(row["backlogs"]),
                cgpa=0,
                email=row.get("email", ""),
                phone=row.get("phone", "")
            ))

            # create login for student
            db.session.add(User(
                username=roll,
                password=generate_password_hash("1234"),
                role="student"
            ))

        db.session.commit()

    return redirect("/admin")
@app.route("/update_student/<roll>", methods=["GET", "POST"])
def update_student(roll):
    student = Student.query.get(roll)

    if request.method == "POST":
        student.name = request.form["name"]
        student.year = request.form["year"]
        student.grade = request.form["grade"]
        student.backlogs = int(request.form["backlogs"])
        student.email = request.form["email"]
        student.phone = request.form["phone"]

        db.session.commit()
        return redirect("/admin")

    return render_template("edit_student.html", s=student)

@app.route("/delete_student/<roll>")
def delete_student(roll):
    student = Student.query.get(roll)

    # delete marks also (important)
    StudentMark.query.filter_by(roll_no=roll).delete()

    # delete login user
    User.query.filter_by(username=roll).delete()

    db.session.delete(student)
    db.session.commit()

    return redirect("/admin")

@app.route("/update_faculty/<fid>", methods=["GET","POST"])
def update_faculty(fid):
    faculty = Faculty.query.get(fid)

    if request.method == "POST":
        faculty.name = request.form["name"]
        faculty.branch = request.form["branch"]
        faculty.salary = int(request.form["salary"])
        faculty.performance = request.form["performance"]
        faculty.specialization = request.form["specialization"]
        faculty.achievements = request.form["achievements"]

        db.session.commit()
        return redirect("/admin")

    return render_template("edit_faculty.html", f=faculty)

@app.route("/delete_faculty/<fid>")
def delete_faculty(fid):
    Faculty.query.filter_by(faculty_id=fid).delete()
    User.query.filter_by(username=fid).delete()
    db.session.commit()
    return redirect("/admin")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)