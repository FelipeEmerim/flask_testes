import os


def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        raise Exception(message)


UPLOAD_FOLDER = '/home/emerim/FELIPE_EMERIN/flask-teste/uploads'


postgres_url = get_env_variable("POSTGRES_URL")
postgres_user = get_env_variable("POSTGRES_USER")
postgres_pw = get_env_variable("POSTGRES_PW")
postgres_db = get_env_variable("POSTGRES_DB")

db_url = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=postgres_user, pw=postgres_pw, url=postgres_url,
                                                               db=postgres_db)

SQLALCHEMY_DATABASE_URI = db_url
SQLALCHEMY_TRACK_MODIFICATIONS = False  # silence the deprecation warning
SECRET_KEY = os.urandom(16)
DEBUG = True
