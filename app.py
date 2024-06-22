from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/vilaska')
def vilaska():
    return render_template('vilaska.html')

@app.route('/vilaska_lobby')
def vilaska_lobby():
    return render_template('vilaska_lobby.html')

@app.route('/vilaska_list')
def vilaska_list():
    return render_template('vilaska_list.html')

@app.route('/vilaska_complete')
def vilaska_complete():
    return render_template('vilaska_complete.html')


app.run(debug=True)