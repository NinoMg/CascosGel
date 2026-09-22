import os
from dotenv import load_dotenv

load_dotenv()

# Obtener URL de la base de datos
db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://usuario_cascos:mi_password_segura@localhost:5432/cascosgel_db')

# Asegurar que SQLAlchemy utilice el driver psycopg v3
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_dev_key')
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
