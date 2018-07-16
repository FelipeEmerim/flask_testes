import os

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, flash, send_from_directory, url_for, session
import simplejson as json
from werkzeug.exceptions import abort
from werkzeug.utils import redirect, secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy import text
from wtforms import Form, BooleanField, StringField, PasswordField, validators

app = Flask(__name__, static_url_path='/static')
app.config.from_envvar('APP_SETTINGS')
db = SQLAlchemy(app)


EXTENSION = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSION


class Pessoa(db.Model):  # tables defined like this are automatically create by db.create_all()

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(30), unique=True)  # needs a primary key
    email = db.Column(db.String(100))
    senha = db.Column(db.String(500))

    def __init__(self, nome, email, senha):

        self.nome = nome
        self.email = email
        self.senha = generate_password_hash(senha)


@app.before_request
def check_login():

    print(request.path)
    if 'user' not in session and request.path != '/login' and request.endpoint != 'static':
        return redirect('/login')


@app.route('/')
def index():
    return render_template('index.html')


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


@app.route('/login', methods=['POST', 'GET'])
def login():

    if 'user' in session:
        return redirect('/')

    form = criaLogin(request.form)

    if request.method == 'POST' and form.validate():
        pessoa = Pessoa.query.filter_by(nome=form.nome.data.strip()).first()
        if not pessoa:
            flash('Usuario não existe')
            return render_template('login.html', form=form)

        if not check_password_hash(pessoa.senha, form.senha.data):
            flash('senha incorreta')
            return render_template('login.html', form=form)

        session['user'] = form.nome.data
        return redirect('/')

    return render_template('login.html', form=form)


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


class criaLogin(Form):
    nome = StringField('Nome do usuario', [validators.Length(min=4, max=25)], render_kw={"placeholder": "Usuário"})
    senha = PasswordField('Senha', [validators.DataRequired(),
        validators.Regexp('^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{5,}$',
                          message="a senha precisa conter um numero e uma letra maiuscula")
    ], render_kw={"placeholder": "Senha"})


@app.route('/usuario/login2', methods=['GET', 'POST'])
def user_login2():

    if 'user' in session:
        return redirect('/usuario/logged2')

    form = criaLogin(request.form)

    if request.method == 'POST' and form.validate():
        pessoa = Pessoa.query.filter_by(nome=form.nome.data.strip()).first()
        if not pessoa:
            flash('Usuario não existe')
            return render_template('login2.html', form=form)

        if not check_password_hash(pessoa.senha, form.senha.data):
            flash('senha incorreta')
            return render_template('login2.html', form=form)

        session['user'] = form.nome.data
        flash('Você esta logado como '+session['user'])
        return redirect('/')

    return render_template('login2.html', form=form)


@app.route('/usuario/logged2', methods=['GET'])
def user_logged2():

    if request.args.get('logout'):
        session.pop('user', None)
        return redirect('/usuario/login2')

    return render_template('logged2.html', user=session['user'])


@app.route('/login')
def user_login():

    return render_template('login.html', form=form)


@app.route('/usuario/logged', methods=['POST', 'GET'])
def user_logged():

    if 'user' not in session:
        name = request.form['name']
        session['user'] = name

    return render_template('logged_in.html')


@app.route('/usuario/logout', methods=['GET', 'POST'])
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect('/usuario/login')


class cria_cadastro(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Regexp('^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{5,}$', message="a senha precisa conter um numero e uma letra maiuscula")
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/usuario/cadastro', methods=['GET', 'POST'])
def cadastro():
    form = cria_cadastro(request.form)

    if request.method == 'POST' and form.validate():

        print('sadas')
        pessoa = Pessoa(form.username.data.strip(), form.email.data.strip(), form.password.data)
        db.session.add(pessoa)
        db.session.commit()

    return render_template('cadastro.html', form=form, users=Pessoa.query.all())


@app.route('/usuario/deleta<int:user_id>', methods=['GET'])
def deleta(user_id):

    user = Pessoa.query.filter_by(id=user_id).first()

    if not user:
        flash('Usuario não encontrado')
        return redirect('/usuario/cadastro')

    flash('usuario '+user.nome+' deletado')
    db.session.delete(user)
    db.session.commit()

    return redirect('/usuario/cadastro')


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

        data = {"nome": "Felipe", "email": 'lip@gmail.com', 'senha': '123'}
        query = text('''INSERT INTO Pessoa(nome, email, senha) VALUES (:nome, :email, :senha)''')   # always use text to create query
        con.execute(query, nome='Carina', email='carina@gmail.com', senha=123)  # inserting using arguments
        con.execute(query, **data)  # inserting using dictionary

        query = text('''UPDATE Pessoa SET email = :email WHERE nome = :nome''')
        con.execute(query, email='carina@sadas.com', nome='Carina')  # both ways work with update

        query = '''SELECT * FROM Pessoa'''
        result = con.execute(query)
        print(result.fetchall())

    con.close()  # close the connection

    print('It worked my friend')





