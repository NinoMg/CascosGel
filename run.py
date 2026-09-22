from app import create_app
from app.models import db, Usuario, Casco

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Borra las tablas desactualizadas y las crea con la estructura correcta
        db.drop_all()
        db.create_all()
        print(">>> Tablas recreadas correctamente en PostgreSQL.")

        # Crear usuario administrador por defecto
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(username='admin', nombre='Administrador Fundación')
            admin.set_password('admin123')
            db.session.add(admin)

            # Cargar cascos de muestra
            if Casco.query.count() == 0:
                for i in range(1, 11):
                    casco = Casco(codigo_identificador=f"C-{i:03d}", estado='disponible')
                    db.session.add(casco)

            db.session.commit()
            print(">>> Usuario 'admin' (pass: admin123) y cascos creados con éxito.")

    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
