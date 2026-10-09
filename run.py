from app import create_app
from app.models import db, Usuario, Stock

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print(">>> Tablas verificadas correctamente en PostgreSQL.")

        Stock.obtener()   # crea la fila de stock (con 0 cascos) si no existe

        # Crear usuario administrador por defecto
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(username='admin', nombre='Administrador Fundación')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print(">>> Usuario 'admin' (pass: admin123) creado con éxito.")

    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
