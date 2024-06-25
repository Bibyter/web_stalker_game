from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, UserMixin, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my.db'
app.config["SECRET_KEY"] = '3b05ed0ff4efbd12ea076b94f9f42b225a81d8529881c8cd473e7a2f6f11'

login_manager = LoginManager(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)
    gamepr = db.relationship('GameProfile', uselist=False)

    def __repr__(self):
        return f'<user {self.login}:{self.id}>'

    def get_id(self):
        return self.id

    def get_login(self):
        return self.login


class GameProfile(db.Model):
    __tablename__ = 'game_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    money = db.Column(db.Integer)
    radiation = db.Column(db.Integer)

    def __repr__(self):
        return f'<game_profile {self.user_id}>'





@app.route('/')
@login_required
def home():
    return render_template('index.html')


#login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user = Users(
            login=request.form['login'], 
            psw=generate_password_hash(request.form['psw'])
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        member = Users.query.filter_by(login=request.form['login']).first()
        print(member)
        if member and check_password_hash(member.psw, request.form['psw']):
            login_user(member)
            flash(f'Добро пожаловать {member.login}', 'success')
            return redirect(url_for('home'))
        else:
            flash('Имя пользователя или пароль не совпадает, повторите попытку!', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из профиля" , "success")
    return redirect(url_for("login"))

# vilaska
@app.route('/vilaska')
@login_required
def vilaska():
    return render_template('vilaska.html')

@app.route('/vilaska_lobby')
@login_required
def vilaska_lobby():
    return render_template('vilaska_lobby.html')

@app.route('/vilaska_list')
@login_required
def vilaska_list():
    return render_template('vilaska_list.html')

@app.route('/vilaska_complete')
@login_required
def vilaska_complete():
    return render_template('vilaska_complete.html')


if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()

    app.run(debug=True, host='0.0.0.0')