from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='admin')
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Paciente(db.Model):
    __tablename__ = 'pacientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono1 = db.Column(db.String(20), nullable=False)
    telefono2 = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=False)
    periodo = db.Column(db.String(50), nullable=False)  # ej: "6 meses"
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    prestamos = db.relationship('Prestamo', backref='paciente', lazy=True)
    donaciones = db.relationship('Donacion', backref='paciente', lazy=True)

    def to_dict(self):
        # Cuenta los cascos prestados activos
        cascos_prestados_cant = sum(p.cantidad for p in self.prestamos if p.estado == 'activo')
        return {
            'id': self.id,
            'nombre': self.nombre,
            'telefono1': self.telefono1,
            'telefono2': self.telefono2,
            'direccion': self.direccion,
            'periodo': self.periodo,
            'cantidad_cascos_prestados': cascos_prestados_cant,
            'creado_en': self.creado_en.isoformat()
        }

class Casco(db.Model):
    __tablename__ = 'cascos'

    id = db.Column(db.Integer, primary_key=True)
    codigo_identificador = db.Column(db.String(20), unique=True, nullable=False)
    estado = db.Column(db.String(20), default='disponible')  # disponible, prestado, mantenimiento, baja
    origen = db.Column(db.String(20), default='fundacion')   # fundacion, donacion
    observaciones = db.Column(db.Text, nullable=True)

    prestamos = db.relationship('Prestamo', backref='casco', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'codigo_identificador': self.codigo_identificador,
            'estado': self.estado,
            'origen': self.origen,
            'observaciones': self.observaciones
        }

class Prestamo(db.Model):
    __tablename__ = 'prestamos'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    casco_id = db.Column(db.Integer, db.ForeignKey('cascos.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    fecha_prestamo = db.Column(db.Date, nullable=False, default=date.today)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), default='activo')  # activo, vencido, devuelto
    observaciones = db.Column(db.Text, nullable=True)

    def to_dict(self):
        # Actualización dinámica de estado vencido
        estado_actual = self.estado
        if estado_actual == 'activo' and self.fecha_vencimiento < date.today():
            estado_actual = 'vencido'

        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'paciente_nombre': self.paciente.nombre if self.paciente else None,
            'paciente_telefono1': self.paciente.telefono1 if self.paciente else None,
            'casco_id': self.casco_id,
            'casco_codigo': self.casco.codigo_identificador if self.casco else None,
            'cantidad': self.cantidad,
            'fecha_prestamo': self.fecha_prestamo.isoformat(),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat(),
            'fecha_devolucion': self.fecha_devolucion.isoformat() if self.fecha_devolucion else None,
            'estado': estado_actual,
            'observaciones': self.observaciones
        }

class Donacion(db.Model):
    __tablename__ = 'donaciones'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    donante_nombre = db.Column(db.String(100), nullable=True)
    cantidad_cascos = db.Column(db.Integer, nullable=False, default=1)
    fecha_donacion = db.Column(db.Date, default=date.today)
    detalle = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'donante_nombre': self.donante_nombre or (self.paciente.nombre if self.paciente else 'Anónimo'),
            'cantidad_cascos': self.cantidad_cascos,
            'fecha_donacion': self.fecha_donacion.isoformat(),
            'detalle': self.detalle
        }
