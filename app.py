import os
import psycopg
from flask import Flask, render_template, jsonify


def create_app():
    app = Flask(__name__)

    @app.get('/')
    def home():
        return render_template('index.html',
                               version=os.getenv('APP_VERSION', 'v1'),
                               environment=os.getenv('APP_ENV', 'local'))

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    @app.get('/version')
    def version():
        return jsonify(version=os.getenv('APP_VERSION', 'v1'),
                       environment=os.getenv('APP_ENV', 'local'))
    
    @app.get("/ready")
    def ready():
        db_config = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT", "5432"),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }

        if not all(db_config.values()):
            return jsonify(
                status="not_ready",
                reason="database_not_configured",
            ), 503

        try:
            with psycopg.connect(
                **db_config,
                connect_timeout=3,
                options="-c statement_timeout=2000",
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()

            if result != (1,):
                return jsonify(status="not_ready"), 503

        except psycopg.Error as error:
            app.logger.warning(
                "Database readiness check failed: %s",
                type(error).__name__,
            )
            return jsonify(
                status="not_ready",
                reason="database_unavailable",
            ), 503

        return jsonify(status="ready", database="connected")
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
