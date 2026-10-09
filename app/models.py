from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

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
    ...
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    prestamos = db.relationship('Prestamo', backref='paciente', lazy=True)

    def to_dict(self):
        # Cuenta los cascos que siguen en manos del paciente (activos y vencidos)
        cascos_prestados_cant = sum(p.cantidad for p in self.prestamos if p.fecha_devolucion is None)
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



class Prestamo(db.Model):
    __tablename__ = 'prestamos'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)   
    cantidad = db.Column(db.Integer, default=1)
    fecha_prestamo = db.Column(db.Date, nullable=False, default=date.today)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)

    # en Prestamo: borrar casco_id y la columna estado, y agregar:
    @property
    def estado(self):
        if self.fecha_devolucion:
            return 'devuelto'
        if self.fecha_vencimiento < date.today():
            return 'vencido'
        return 'activo'

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
            'cantidad': self.cantidad,
            'fecha_prestamo': self.fecha_prestamo.isoformat(),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat(),
            'fecha_devolucion': self.fecha_devolucion.isoformat() if self.fecha_devolucion else None,
            'estado': estado_actual,
            'observaciones': self.observaciones
        }


class Stock(db.Model):
    __tablename__ = 'stock'

    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer, nullable=False, default=0)          # cascos de la fundación, sin contar bajas
    mantenimiento = db.Column(db.Integer, nullable=False, default=0)
    baja = db.Column(db.Integer, nullable=False, default=0)

    @staticmethod
    def obtener():
        # Siempre hay una única fila; si no existe, se crea
        stock = Stock.query.first()
        if not stock:
            stock = Stock()
            db.session.add(stock)
            db.session.commit()
        return stock

    def prestados(self):
        # Todo préstamo sin devolver cuenta, esté vencido o no
        return db.session.query(
            func.coalesce(func.sum(Prestamo.cantidad), 0)
        ).filter(Prestamo.fecha_devolucion.is_(None)).scalar()

    def disponibles(self):
        return self.total - self.mantenimiento - self.prestados()

    def to_dict(self):
        return {
            'total': self.total,
            'disponibles': self.disponibles(),
            'prestados': self.prestados(),
            'mantenimiento': self.mantenimiento,
            'baja': self.baja
        }
