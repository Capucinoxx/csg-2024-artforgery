import os

MONGODB_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGODB_PORT = int(os.environ.get('MONGO_PORT', '27017'))
MONGODB_DB = os.environ.get('MONGO_DBNAME', 'hackme')

SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key')
ROUND_DURATION = 35 * 60
BREAK_DURATION = 5 * 60

IMAGES_FOLDER = 'app/challenges-img'

FLASK_DEBUG = False
FLASK_ENV='production'