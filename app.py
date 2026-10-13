import os
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

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
