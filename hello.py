import os

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, flash, send_from_directory, url_for, session
import simplejson as json
from werkzeug.exceptions import abort
from werkzeug.utils import redirect, secure_filename
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy import text

app = Flask(__name__, static_url_path='/static')
app.config.from_envvar('APP_SETTINGS')
db = SQLAlchemy(app)


EXTENSION = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSION


class Pessoa(db.Model):  # tables defined like this are automatically create by db.create_all()
    nome = db.Column(db.String(30), primary_key=True)  # needs a primary key
    idade = db.Column(db.Integer)


@app.cli.command('resetdb')
def resetdb_command():
    """Destroys and creates the database + tables."""
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if database_exists(db_url):
        print('Deleting database.')
        drop_database(db_url)
    if not database_exists(db_url):
        print('Creating database.')
        create_database(db_url)

    print('Creating tables.')
    db.create_all()    # creates all tables defined as classes that extends models
    db.session.commit()
    # example of usage
    con = db.engine.connect()    # creates a connection object
    query = text('''SELECT VERSION()''')     # creates a query to select the version of postgres
    transaction = con.begin()   # begins the transaction
    try:       # example of simple transaction
        result = con.execute(query)
        print(result.fetchall())
        transaction.commit()
    except SQLAlchemyError:
        transaction.rollback()
        print('transaction rolled back due to errors')

    with con.begin():      # example of transaction using the context manager
        # query = text('CREATE TABLE Pessoa(nome TEXT, idade INTEGER);')  # create table using raw sql
        # con.execute(query)

        data = {"nome": "Felipe", "idade": 20}
        query = text('''INSERT INTO Pessoa(nome, idade) VALUES (:nome, :idade)''')   # always use text to create query
        con.execute(query, nome='Carina', idade=20)  # inserting using arguments
        con.execute(query, **data)  # inserting using dictionary

        query = text('''UPDATE Pessoa SET idade = :idade WHERE nome = :nome''')
        con.execute(query, idade=28, nome='Carina')  # both ways work with update

        query = '''SELECT * FROM Pessoa'''
        result = con.execute(query)
        print(result.fetchall())

    con.close()  # close the connection

    print('It worked my friend')


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

