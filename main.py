from flask import Flask, jsonify, request, abort, redirect, url_for, render_template
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import sqlalchemy
from sqlalchemy import desc
import pymysql

host = 'localhost'
user = 'root'
passwd = '123456789'
database = 'Evaluation'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + user + ':' + passwd + '@' + host + '/' + database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app.app_context().push()
app.debug = True
bcryptObj = Bcrypt(app)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Users(db.Model):
    user_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    user_password = db.Column(db.String(1000), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    authenticated = db.Column(db.Boolean, default=False)

    def is_active(self):
        return True

    def get_id(self):
        return self.user_id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

class ta(db.Model):
    ta_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    native_english_speaker = db.Column(db.Boolean, default=False, nullable=False)
    Course_instructor = db.Column(db.String(255), nullable=False)
    course = db.Column(db.String(255), nullable=False)
    semester = db.Column(db.String(255), nullable=False)
    class_size = db.Column(db.Integer,default=0, nullable=False)
    class_attribute=db.Column(db.String(255), nullable=False)
    info_created_by = db.Column(db.Integer, db.ForeignKey(Users.user_id), nullable=False)

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.ta_id,
            'native_english_speaker': self.native_english_speaker,
            "Course_instructor": self.Course_instructor,
            "course": self.course,
            "semester": self.semester,
            "class_size": self.class_size,
            "class_attribute": self.class_attribute
        }



db.create_all()


@login_manager.user_loader
def user_loader(user_id):
    return Users.query.get(user_id)


# index page
@app.route("/", methods=['GET'])
def index():
    ta_data_a = ta.query.all()
    context = {"data": [ta_data.serialized for ta_data in ta_data_a]}
    return render_template("index.html", ta_data_html=context['data'])



# login page
@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_email = request.form.get('username')
        user_password = request.form.get('password')
        user_data = Users.query.filter_by(user_email=user_email).first()
        if user_data:
            pass
        else:
            message = {"data": "Wrong Username"}
            return render_template("login.html", result=message)

        if bcryptObj.check_password_hash(user_data.user_password, user_password):
            user_data.authenticated = True
            db.session.add(user_data)
            db.session.commit()
            login_user(user_data, remember=True)
            url = f"/user/{user_data.user_id}"
            return redirect(url)
        else:
            message = {"data": "Wrong Password"}
            return render_template("login.html", result=message)
    if request.method == 'GET':
        return render_template('login.html')



# userpage
@app.route("/user/<int:user_id>", methods=['POST', 'GET'])
@login_required
def user(user_id):
    if request.method == 'GET':
        ta_data_a = ta.query.filter_by(info_created_by=user_id)
        context = {"data": [ta_data.serialized for ta_data in ta_data_a]}
        return render_template("home.html", ta_data_html=context['data'])



# register page
@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_email = request.form.get('username')
        user_data = Users.query.filter_by(user_email=user_email).first()
        if user_data:
            message = {"data": " Username exists"}
            return render_template("register.html", result=message)
        else:
            pass
        user_password = request.form.get('password')
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        hashPassword = bcryptObj.generate_password_hash(user_password)
        user = Users(user_email=user_email, user_password=hashPassword, first_name=first_name, last_name=last_name)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return render_template("error.html", error=e)

    elif request.method == 'GET':
        return render_template('register.html')


#add_ta_data 
@app.route("/add_ta_data", methods=['POST', 'GET'])
@login_required
def add_ta_data():
    if request.method == 'POST':
        user = current_user
        Course_instructor = request.form.get('Course_instructor')
        course = request.form.get('course')
        class_size = request.form.get('class_size')
        class_attribute = request.form.get('class_attribute')
        semester = request.form.get('semester')
        native_english_speaker = False
        if request.form.get('native_english_speaker') == "true":
            native_english_speaker = True
        info_created_by = user.user_id
        ta_data = ta(Course_instructor=Course_instructor, course=course, class_size=class_size, 
                     class_attribute=class_attribute, semester=semester, native_english_speaker=native_english_speaker,
                      info_created_by=info_created_by)
        try:
            db.session.add(ta_data)
            db.session.commit()
        except Exception as e:
            return render_template("error.html", error=e)
        url = f"/user/{user.user_id}"
        return redirect(url)

    elif request.method == 'GET':
        user = current_user
        data = {"userID": user.user_id}
        return render_template("add_ta_data.html", result=data)


   
@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route("/fetch_data/<int:ta_id>", methods=['POST', 'GET'])
@login_required
def fetch_data(ta_id):
    if request.method == 'GET':
        user = current_user
        ta_data = ta.query.filter_by(ta_id=ta_id).first()
        context = {"data": [ta_data.serialized], "user": user.user_id}
        return render_template("ta_data.html", ta_data_a=context)
    

@app.route("/update_data/<int:ta_id>", methods=['POST', 'GET'])
@login_required
def update_blog(ta_id):
    if request.method == 'POST':
        ta_data = ta.query.filter_by(ta_id=ta_id).first()
        Course_instructor = request.form.get('Course_instructor')
        course = request.form.get('course')
        class_size = request.form.get('class_size')
        class_attribute = request.form.get('class_attribute')
        if request.form.get('native_english_speaker') == "true":
            native_english_speaker = True
        else:
            native_english_speaker = False
        if Course_instructor:
            ta_data.Course_instructor = Course_instructor
        if course:
            ta_data.course = course
        if class_size:
            ta_data.class_size = class_size
        if class_attribute:
            ta_data.class_attribute = class_attribute
        if native_english_speaker:
            ta_data.native_english_speaker = native_english_speaker
        db.session.commit()
        url = f'/fetch_data/{ta_id}'
        return redirect(url)
    elif request.method == 'GET':
        user = current_user
        ta_data = ta.query.filter_by(ta_id=ta_id).first()
        context = {"data": [ta_data.serialized], "user": user.user_id}
        return render_template("edit_data.html", result=context)



@app.route("/delete_data/<int:ta_id>", methods=['DELETE', 'GET'])
@login_required
def delete_blog(ta_id):
    if request.method == 'GET':
        user = current_user
        data = ta.query.filter_by(ta_id=ta_id).first()
        try:
            db.session.delete(data)
            db.session.commit()
        except:
            pass
        url = f"/user/{user.user_id}"
        return redirect(url)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1048, debug=True)