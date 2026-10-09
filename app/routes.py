from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import date
from app.models import db, Usuario, Paciente, Prestamo, Stock

api = Blueprint('api', __name__)

# --- AUTENTICACIÓN ---
@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    usuario = Usuario.query.filter_by(username=username).first()
    if not usuario or not usuario.check_password(password):
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    access_token = create_access_token(identity=str(usuario.id))

    return jsonify({
        'access_token': access_token,
        'token': access_token,
        'usuario': {
            'id': usuario.id,
            'nombre': usuario.nombre,
            'rol': usuario.rol
        }
    }), 200


# --- PACIENTES ---
@api.route('/pacientes', methods=['GET'])
@jwt_required()
def get_pacientes():
    pacientes = Paciente.query.all()
    return jsonify([p.to_dict() for p in pacientes]), 200

@api.route('/pacientes', methods=['POST'])
@jwt_required()
def create_paciente():
    data = request.get_json() or {}
    nombre = data.get('nombre')
    telefono1 = data.get('telefono1')
    direccion = data.get('direccion')
    periodo = data.get('periodo')

    if not nombre or not telefono1 or not direccion or not periodo:
        return jsonify({'error': 'Faltan campos obligatorios'}), 400

    nuevo_paciente = Paciente(
        nombre=nombre,
        telefono1=telefono1,
        telefono2=data.get('telefono2'),
        direccion=direccion,
        periodo=periodo
    )
    db.session.add(nuevo_paciente)
    db.session.commit()
    return jsonify(nuevo_paciente.to_dict()), 201


# --- STOCK ---
@api.route('/stock', methods=['GET'])
@jwt_required()
def get_stock():
    return jsonify(Stock.obtener().to_dict()), 200

@api.route('/stock/ingreso', methods=['POST'])
@jwt_required()
def ingresar_cascos():
    data = request.get_json() or {}
    try:
        cantidad = int(data.get('cantidad', 0))
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad < 1:
        return jsonify({'error': 'La cantidad debe ser al menos 1'}), 400

    stock = Stock.obtener()
    stock.total += cantidad
    db.session.commit()
    return jsonify(stock.to_dict()), 201

def _leer_cantidad():
    data = request.get_json() or {}
    try:
        cantidad = int(data.get('cantidad', 0))
    except (TypeError, ValueError):
        cantidad = 0
    return data, cantidad

@api.route('/stock/mantenimiento', methods=['POST'])
@jwt_required()
def mover_mantenimiento():
    data, cantidad = _leer_cantidad()
    accion = data.get('accion')  # 'enviar' o 'recuperar'
    if cantidad < 1:
        return jsonify({'error': 'La cantidad debe ser al menos 1'}), 400

    stock = Stock.obtener()
    if accion == 'enviar':
        if cantidad > stock.disponibles():
            return jsonify({'error': f'Solo hay {stock.disponibles()} cascos disponibles'}), 400
        stock.mantenimiento += cantidad
    elif accion == 'recuperar':
        if cantidad > stock.mantenimiento:
            return jsonify({'error': f'Solo hay {stock.mantenimiento} cascos en mantenimiento'}), 400
        stock.mantenimiento -= cantidad
    else:
        return jsonify({'error': 'Acción inválida'}), 400

    db.session.commit()
    return jsonify(stock.to_dict()), 200

@api.route('/stock/baja', methods=['POST'])
@jwt_required()
def dar_de_baja():
    data, cantidad = _leer_cantidad()
    origen = data.get('origen')  # 'disponible' o 'mantenimiento'
    if cantidad < 1:
        return jsonify({'error': 'La cantidad debe ser al menos 1'}), 400

    stock = Stock.obtener()
    if origen == 'disponible':
        if cantidad > stock.disponibles():
            return jsonify({'error': f'Solo hay {stock.disponibles()} cascos disponibles'}), 400
    elif origen == 'mantenimiento':
        if cantidad > stock.mantenimiento:
            return jsonify({'error': f'Solo hay {stock.mantenimiento} cascos en mantenimiento'}), 400
        stock.mantenimiento -= cantidad
    else:
        return jsonify({'error': 'Origen inválido'}), 400

    stock.total -= cantidad
    stock.baja += cantidad
    db.session.commit()
    return jsonify(stock.to_dict()), 200

@api.route('/cascos/resumen', methods=['GET'])
@jwt_required()
def get_cascos_resumen():
    stock = Stock.obtener()
    vencidos = Prestamo.query.filter(
        Prestamo.fecha_devolucion.is_(None),
        Prestamo.fecha_vencimiento < date.today()
    ).count()
    return jsonify({
        'total': stock.total,
        'prestados': stock.prestados(),
        'disponibles': stock.disponibles(),
        'vencidos': vencidos
    }), 200
