from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import Dataset, Analysis
from app import db
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard', methods=['GET'])
# @jwt_required() # Uncomment for JWT auth
def get_dashboard_stats():
    # Example logic
    datasets = Dataset.query.count()
    analyses = Analysis.query.count()
    return jsonify({
        "status": "success",
        "data": {
            "total_datasets": datasets,
            "total_analyses": analyses,
            "system_status": "online"
        }
    })

@api_bp.route('/rules/<int:analysis_id>', methods=['GET'])
def get_rules(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    return jsonify({
        "status": "success",
        "dataset": analysis.dataset.original_name,
        "parameters": {
            "min_support": analysis.min_support,
            "min_confidence": analysis.min_confidence
        },
        "rules": json.loads(analysis.results_json)
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0"})
