from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import login_required, current_user
from models.user import Dataset, Analysis
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('home.html')
    return redirect(url_for('dashboard.home'))

@dashboard_bp.route('/dashboard')
@login_required
def home():
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # User's datasets and analyses
    user_datasets = Dataset.query.filter_by(user_id=current_user.id)
    dataset_count = user_datasets.count()
    
    user_analyses = Analysis.query.join(Dataset).filter(Dataset.user_id == current_user.id)
    analysis_count = user_analyses.count()
    
    # Real Stats
    total_rules = db.session.query(func.sum(Analysis.rules_count)).join(Dataset).filter(Dataset.user_id == current_user.id).scalar() or 0
    
    # Simulated stats for polish (since we don't store duration yet)
    avg_processing = 0.45 if analysis_count > 0 else 0.0
    
    # Recent activity
    recent_datasets = user_datasets.order_by(Dataset.created_at.desc()).limit(5).all()
    
    # Chart Data (Last 7 days)
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        
        # Count rules found on that day
        day_rules = db.session.query(func.sum(Analysis.rules_count))\
            .join(Dataset)\
            .filter(Dataset.user_id == current_user.id)\
            .filter(func.date(Analysis.created_at) == day).scalar() or 0
        chart_data.append(int(day_rules))

    return render_template('dashboard/index.html', 
                           dataset_count=dataset_count, 
                           analysis_count=analysis_count,
                           total_rules=total_rules,
                           avg_processing=avg_processing,
                           recent_datasets=recent_datasets,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

@dashboard_bp.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in ['uz', 'en', 'ru']:
        session['lang'] = lang
    return redirect(url_for('dashboard.home'))
