from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Import models after db initialization to avoid circular imports
    with app.app_context():
        from models import User, Trip

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({'status': 'ok', 'message': 'Planventure API'})

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy'})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
