from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import Config
from app.models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    CORS(app)
    db.init_app(app)
    JWTManager(app)

    # Ruta para servir la interfaz gráfica
    @app.route('/')
    def index():
        return render_template('index.html')

    # Registrar rutas de la API REST
    from app.routes import api
    app.register_blueprint(api, url_prefix='/api')

    # Manejo de errores 404
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso no encontrado'}), 404

    return app
