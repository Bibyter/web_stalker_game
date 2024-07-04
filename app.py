from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, UserMixin, logout_user
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my.db'
app.config["SECRET_KEY"] = '3b05ed0ff4efbd12ea076b94f9f42b225a81d8529881c8cd473e7a2f6f11'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

VilaskaStateLobby = 0
VilaskaStateGame = 1
VilaskaStateWin = 2
VilaskaStateFail = 3



class VilaskaPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vilaska_id = db.Column(db.Integer, db.ForeignKey('vilaska.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    health = db.Column(db.Integer, nullable=False, default=0)
    attack_cooldown = db.Column(db.Integer, nullable=False, default=0)

    def take_damage(self, amount:int):
        self.health = max(self.health - amount, 0)

    def is_alive(self):
        return self.health > 0


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)
    gamepr = db.relationship('GameProfile', uselist=False, backref='user')
    vilaska_player = db.relationship('VilaskaPlayer', uselist=False, backref='user')

    def __repr__(self):
        return f'<user {self.login}:{self.id}>'

    def get_id(self):
        return self.id

    def get_login(self):
        return self.login

current_user: Users



class GameProfile(db.Model):
    __tablename__ = 'game_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    money = db.Column(db.Integer, nullable=False, default=0)
    radiation = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<game_profile {self.user_id}>'


class Vilaska(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    state = db.Column(db.Integer, nullable=False, default=0) # 0-lobby, 1-play, 2-complete
    players = db.relationship('VilaskaPlayer', uselist=True, backref='vilaska')
    enemy_hp = db.Column(db.Integer, nullable=False, default=0)
    log_messages = db.relationship('VilaskaLogMessage', uselist=True, backref='vilaska')

    def is_all_player_of_dead(self):
        for player in self.players:
            if player.is_alive():
                return False
        return True
    
    def enemy_take_damage(self, amount:int):
        self.enemy_hp = max(self.enemy_hp - amount, 0)


class VilaskaLogMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vilaska_id = db.Column(db.Integer, db.ForeignKey('vilaska.id'))
    value = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)



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
            psw=generate_password_hash(request.form['psw']),
            gamepr=GameProfile()
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
    vilaska_player = current_user.vilaska_player
    if not vilaska_player:
        print('игрок не входит в состам вылазки')
        return redirect(url_for('vilaska_list'))
    vilaska: Vilaska = Vilaska.query.get(vilaska_player.vilaska_id)
    if vilaska.state == VilaskaStateGame:
        return redirect(url_for('vilaska_game'))
    return render_template('vilaska_lobby.html', vilaska=vilaska)

@app.route('/vilaska_list')
@login_required
def vilaska_list():
    if current_user.vilaska_player:
        return redirect(url_for('vilaska_lobby'))
    return render_template('vilaska_list.html', vilaska_list=Vilaska.query.filter_by(state=VilaskaStateLobby).all())


@app.route('/vilaska_create', methods=['POST'])
@login_required
def vilaska_create():
    if request.method == 'POST':
        v = Vilaska(
            name = request.form['name']
        )
        db.session.add(v)
        # vp = VilaskaPlayer(
        #     vilaska_id = v.id,
        #     user_id = current_user.get_id()
        # )
        #db.session.add(vp)
        db.session.commit()
    return redirect(url_for('vilaska_list'))


@app.route('/vilaska_leave')
@login_required
def vilaska_leave():
    if current_user.vilaska_player:
        db.session.delete(current_user.vilaska_player)
        db.session.commit()

    return redirect(url_for('vilaska_list'))



@app.route('/vilaska_join/<int:vilaska_id>')
@login_required
def vilaska_join(vilaska_id:int):
    vilaska = Vilaska.query.get(vilaska_id)

    if not vilaska:
        print('вылазки с таким id не существует')
        return redirect(url_for('vilaska_list'))

    vilaska_player = VilaskaPlayer.query.filter_by(user_id=current_user.get_id()).first()

    if vilaska_player:
        print(f'Игрок уже находится в другой вылазке {vilaska_player}')
        return redirect(url_for('vilaska_lobby'))
    else:
        new_vilaska_player = VilaskaPlayer(
            vilaska_id = vilaska.id,
            user_id = current_user.get_id(),
        )
        db.session.add(new_vilaska_player)
        db.session.commit()
        return redirect(url_for('vilaska_lobby'))


@app.route('/vilaska_start')
@login_required
def vilaska_start():
    if current_user.vilaska_player:
        vilaska = Vilaska.query.get(current_user.vilaska_player.vilaska_id)
        vilaska.state = VilaskaStateGame
        vilaska.enemy_hp = 100

        for player in vilaska.players:
            player.health = 100
            player.attack_cooldown = 1
            db.session.add(player)

        db.session.add(vilaska)
        db.session.commit()

    return redirect(url_for('vilaska_game'))


@app.route('/vilaska_game')
@login_required
def vilaska_game():
    if current_user.vilaska_player:
        vilaska = Vilaska.query.get(current_user.vilaska_player.vilaska_id)
        if vilaska.state == VilaskaStateGame:
            return render_template('vilaska.html', enemy_hp=vilaska.enemy_hp, player_hp=current_user.vilaska_player.health, vilaska=vilaska)
        if vilaska.state == VilaskaStateWin or vilaska.state == VilaskaStateFail:
            db.session.delete(current_user.vilaska_player)
            db.session.commit()
            return render_template('vilaska_complete.html', is_win=vilaska.state == VilaskaStateWin)
    return redirect(url_for('home'))


@app.route('/vilaska_attack')
@login_required
def vilaska_attack():
    if current_user.vilaska_player:
        vilaska: Vilaska = Vilaska.query.get(current_user.vilaska_player.vilaska_id)
        
        if vilaska.state == VilaskaStateGame and current_user.vilaska_player.health > 0:
            vilaska.enemy_take_damage(10)
            vilaska.log_messages.append(VilaskaLogMessage(value=f'<span class="log_message_nickname">{current_user.get_login()}</span> нанес врагу {10} урона!'))

            if vilaska.enemy_hp <= 0:
                vilaska_finish(vilaska)

            current_user.vilaska_player.take_damage(30)
            vilaska.log_messages.append(VilaskaLogMessage(value=f'<span class="log_message_nickname">{current_user.get_login()}</span> получил в ответ {30} урона!'))

            if vilaska.is_all_player_of_dead():
                vilaska.state = VilaskaStateFail

        db.session.commit()
    return redirect(url_for('vilaska_game'))




def vilaska_finish(vilaska:Vilaska):
    vilaska.state = VilaskaStateWin
    for player in vilaska.players:
        gamepr = player.user.gamepr
        gamepr.money += 50
        gamepr.radiation += 10
        db.session.add(gamepr)


@app.route('/vilaska_complete')
@login_required
def vilaska_complete():
    pass

def update_db():
    with app.app_context():
        db.create_all()

        # for user in Users.query.all():
        #     user.gamepr = GameProfile()

        db.session.commit()

if __name__ == '__main__':
    #update_db()

    app.run(debug=True, host='0.0.0.0')