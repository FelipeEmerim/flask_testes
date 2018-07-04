import os

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, flash, send_from_directory, url_for, session
import simplejson as json
from werkzeug.exceptions import abort
from werkzeug.utils import redirect, secure_filename
from sqlalchemy_utils import database_exists, create_database, drop_database

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(16)

UPLOAD_FOLDER = '/home/emerim/FELIPE_EMERIN/flask-teste/uploads'
EXTENSION = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSION


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


POSTGRES_URL = get_env_variable("POSTGRES_URL")
POSTGRES_USER = get_env_variable("POSTGRES_USER")
POSTGRES_PW = get_env_variable("POSTGRES_PW")
POSTGRES_DB = get_env_variable("POSTGRES_DB")

DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
                                                               db=POSTGRES_DB)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False   # silence the deprecation warning

db = SQLAlchemy(app)


@app.cli.command('resetdb')
def resetdb_command():
    """Destroys and creates the database + tables."""

    if database_exists(DB_URL):
        print('Deleting database.')
        drop_database(DB_URL)
    if not database_exists(DB_URL):
        print('Creating database.')
        create_database(DB_URL)

    print('Creating tables.')
    db.create_all()
    print('Shiny!')


@app.route('/')
def index():
    return 'Bem vindo ao index!'


@app.route('/hello')
def hello():
    return 'Hello World!'


@app.route('/user/<username>')
def show_user(username):
    return 'Welcome {}'.format(username)


@app.route('/number', methods=['GET'])
def show_number():
    nome = request.args.get('nome')
    if not nome:
        nome = 'estranho'
    return 'Seja bem vindo {}'.format(nome)


@app.route('/login')
def login():
    return render_template('hello.html')


@app.route('/logged', methods=['POST'])
def logged_in():
    data = request.get_json()
    return json.dumps({'usuario': data['nome']})


@app.route('/logged_two', methods=['POST'])
def logged_in_two():
    data = request.get_json()
    return render_template('logado.html', usuario=data['nome'])


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        if 'file' not in request.files:

            flash('No selected file')
            return json.dumps({'url': 'error'})

        file = request.files['file']

        if file.filename == '':

            flash('No selected file')
            return json.dumps({'url': 'error'})

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return json.dumps({'url': url_for('uploaded_file', filename=filename), 'name': filename})
        else:
            flash('file not supported')
            return json.dumps({'url': 'error'})

    return render_template('file_input.html')


@app.route('/uploads<filename>')
def uploaded_file(filename):
    if not os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.errorhandler(404)
def send_error(error):
    return render_template('erro.html'), 404


@app.route('/usuario/login')
def user_login():
    if 'user' in session:
        return redirect('/usuario/logged')

    return render_template('user_login.html')


@app.route('/usuario/logged', methods=['POST', 'GET'])
def user_logged():

    if not request.form.get('name') and 'user' not in session:
        return redirect('/usuario/login')

    if 'user' not in session:
        name = request.form['name']
        session['user'] = name

    return render_template('logged_in.html')


@app.route('/usuario/logout', methods=['GET', 'POST'])
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect('/usuario/login')

