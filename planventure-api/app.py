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

    # Register blueprints
    from routes import auth_bp
    app.register_blueprint(auth_bp)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'token_expired',
            'message': 'The token has expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'invalid_token',
            'message': 'Signature verification failed'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'authorization_required',
            'message': 'Request does not contain an access token'
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'token_revoked',
            'message': 'The token has been revoked'
        }), 401

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
