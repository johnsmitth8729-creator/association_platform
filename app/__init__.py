from flask import Flask, session, g, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
import json

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Ensure upload/export directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

    # Multi-language Middleware
    @app.before_request
    def load_translations():
        lang = session.get('lang', 'uz')
        translations_path = os.path.join(app.root_path, 'translations', f'{lang}.json')
        try:
            with open(translations_path, 'r', encoding='utf-8') as f:
                g.translations = json.load(f)
        except FileNotFoundError:
            g.translations = {}

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.dataset.routes import dataset_bp
    from app.apriori.routes import apriori_bp
    from app.analytics.routes import analytics_bp
    from app.admin.routes import admin_bp
    from app.api.routes import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(dataset_bp, url_prefix='/dataset')
    app.register_blueprint(apriori_bp, url_prefix='/apriori')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
