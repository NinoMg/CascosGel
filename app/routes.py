from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import db, Usuario, Casco, Paciente, Prestamo

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


# --- CASCOS E INVENTARIO ---
@api.route('/cascos', methods=['GET'])
@jwt_required()
def get_cascos():
    cascos = Casco.query.all()
    return jsonify([c.to_dict() for c in cascos]), 200

@api.route('/cascos', methods=['POST'])
@jwt_required()
def create_casco():
    data = request.get_json() or {}
    codigo = data.get('codigo_identificador')
    origen = data.get('origen', 'fundacion')
    observaciones = data.get('observaciones', '')

    if not codigo:
        return jsonify({'error': 'El código del casco es obligatorio (ej: C-015)'}), 400

    if Casco.query.filter_by(codigo_identificador=codigo).first():
        return jsonify({'error': f'El casco {codigo} ya se encuentra registrado.'}), 400

    nuevo_casco = Casco(
        codigo_identificador=codigo,
        estado='disponible',
        origen=origen,
        observaciones=observaciones
    )
    db.session.add(nuevo_casco)
    db.session.commit()
    return jsonify(nuevo_casco.to_dict()), 201

@api.route('/cascos/resumen', methods=['GET'])
@jwt_required()
def get_cascos_resumen():
    total = Casco.query.count()
    prestados = Casco.query.filter_by(estado='prestado').count()
    disponibles = Casco.query.filter_by(estado='disponible').count()
    vencidos = Prestamo.query.filter_by(estado='activo').filter(Prestamo.fecha_vencimiento < db.func.current_date()).count()

    return jsonify({
        'total': total,
        'prestados': prestados,
        'disponibles': disponibles,
        'vencidos': vencidos
    }), 200
