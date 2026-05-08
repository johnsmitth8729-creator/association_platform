from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.user import Dataset, Analysis
from app import db
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def index():
    # Gather global stats for the user
    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    analyses = Analysis.query.join(Dataset).filter(Dataset.user_id == current_user.id).all()
    
    total_rules = sum([a.rules_count for a in analyses])
    avg_support = db.session.query(func.avg(Analysis.min_support)).join(Dataset).filter(Dataset.user_id == current_user.id).scalar() or 0
    avg_confidence = db.session.query(func.avg(Analysis.min_confidence)).join(Dataset).filter(Dataset.user_id == current_user.id).scalar() or 0
    
    return render_template('analytics/index.html', 
                           total_datasets=len(datasets),
                           total_analyses=len(analyses),
                           total_rules=total_rules,
                           avg_support=round(avg_support, 3),
                           avg_confidence=round(avg_confidence, 2))
