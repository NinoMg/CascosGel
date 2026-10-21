from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import date
from app.models import db, Usuario, Paciente, Prestamo, Stock
from app.utils import calcular_fecha_vencimiento

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
def _validar_paciente(data):
    campos = {
        'nombre': (data.get('nombre') or '').strip(),
        'telefono1': (data.get('telefono1') or '').strip(),
        'telefono2': (data.get('telefono2') or '').strip() or None,
        'direccion': (data.get('direccion') or '').strip(),
        'periodo': (data.get('periodo') or '').strip(),
    }
    if not (campos['nombre'] and campos['telefono1'] and campos['direccion'] and campos['periodo']):
        return None, 'Faltan campos obligatorios'
    return campos, None

@api.route('/pacientes', methods=['GET'])
@jwt_required()
def get_pacientes():
    pacientes = Paciente.query.order_by(Paciente.nombre).all()
    return jsonify([p.to_dict() for p in pacientes]), 200

@api.route('/pacientes', methods=['POST'])
@jwt_required()
def create_paciente():
    campos, error = _validar_paciente(request.get_json() or {})
    if error:
        return jsonify({'error': error}), 400
    nuevo = Paciente(**campos)
    db.session.add(nuevo)
    db.session.commit()
    return jsonify(nuevo.to_dict()), 201

@api.route('/pacientes/<int:paciente_id>', methods=['PUT'])
@jwt_required()
def update_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente no encontrado'}), 404
    campos, error = _validar_paciente(request.get_json() or {})
    if error:
        return jsonify({'error': error}), 400
    for clave, valor in campos.items():
        setattr(paciente, clave, valor)
    db.session.commit()
    return jsonify(paciente.to_dict()), 200


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

# --- PRÉSTAMOS ---
@api.route('/prestamos', methods=['POST'])
@jwt_required()
def crear_prestamo():
    data = request.get_json() or {}

    try:
        paciente_id = int(data.get('paciente_id'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Seleccioná un paciente'}), 400
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente no encontrado'}), 404

    try:
        cantidad = int(data.get('cantidad', 0))
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad < 1:
        return jsonify({'error': 'La cantidad debe ser al menos 1'}), 400

    stock = Stock.obtener()
    if cantidad > stock.disponibles():
        return jsonify({'error': f'Solo hay {stock.disponibles()} cascos disponibles'}), 400

    hoy = date.today()

    # Fecha de entrega: hoy por defecto; se puede indicar una anterior (préstamos ya en curso)
    fecha_prestamo = hoy
    if data.get('fecha_prestamo'):
        try:
            fecha_prestamo = date.fromisoformat(data['fecha_prestamo'])
        except ValueError:
            return jsonify({'error': 'Fecha de entrega inválida'}), 400
        if fecha_prestamo > hoy:
            return jsonify({'error': 'La fecha de entrega no puede ser futura'}), 400

    if data.get('fecha_vencimiento'):
        try:
            vencimiento = date.fromisoformat(data['fecha_vencimiento'])
        except ValueError:
            return jsonify({'error': 'Fecha de vencimiento inválida'}), 400
    else:
        vencimiento = calcular_fecha_vencimiento(fecha_prestamo, paciente.periodo)

    if vencimiento < fecha_prestamo:
        return jsonify({'error': 'El vencimiento no puede ser anterior a la entrega'}), 400

    prestamo = Prestamo(
        paciente_id=paciente.id,
        cantidad=cantidad,
        fecha_prestamo=fecha_prestamo,
        fecha_vencimiento=vencimiento,
        observaciones=(data.get('observaciones') or '').strip() or None
    )
    db.session.add(prestamo)
    db.session.commit()
    return jsonify(prestamo.to_dict()), 201

@api.route('/prestamos', methods=['GET'])
@jwt_required()
def listar_prestamos():
    estado = request.args.get('estado', 'pendientes')
    consulta = Prestamo.query
    if estado == 'pendientes':
        consulta = consulta.filter(Prestamo.fecha_devolucion.is_(None))
    elif estado == 'vencidos':
        consulta = consulta.filter(Prestamo.fecha_devolucion.is_(None),
                                   Prestamo.fecha_vencimiento < date.today())
    elif estado == 'devueltos':
        consulta = consulta.filter(Prestamo.fecha_devolucion.isnot(None))

    if estado in ('pendientes', 'vencidos'):
        consulta = consulta.order_by(Prestamo.fecha_vencimiento.asc())   # primero los más urgentes
    else:
        consulta = consulta.order_by(Prestamo.fecha_prestamo.desc(), Prestamo.id.desc())

    return jsonify([p.to_dict() for p in consulta.all()]), 200

@api.route('/prestamos/<int:prestamo_id>/devolucion', methods=['POST'])
@jwt_required()
def registrar_devolucion(prestamo_id):
    prestamo = db.session.get(Prestamo, prestamo_id)
    if not prestamo:
        return jsonify({'error': 'Préstamo no encontrado'}), 404
    if prestamo.fecha_devolucion:
        return jsonify({'error': 'Este préstamo ya fue devuelto'}), 400
    prestamo.fecha_devolucion = date.today()
    db.session.commit()
    return jsonify(prestamo.to_dict()), 200