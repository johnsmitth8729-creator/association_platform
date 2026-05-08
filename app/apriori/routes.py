import os
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, make_response, jsonify
from flask_login import login_required, current_user
from models.user import Dataset, Analysis
from app import db
from .engine import MiningEngine

apriori_bp = Blueprint('apriori', __name__)

@apriori_bp.route('/mine', methods=['GET', 'POST'])
@login_required
def mine():
    dataset_id = request.args.get('dataset_id', type=int)
    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    
    if not datasets:
        flash('Avval ma\'lumotlar to\'plamini yuklang', 'warning')
        return redirect(url_for('dataset.upload'))

    selected_dataset = None
    if dataset_id:
        selected_dataset = db.session.get(Dataset, dataset_id)

    if request.method == 'POST':
        dataset_id = request.form.get('dataset_id', type=int)
        min_support = float(request.form.get('min_support', 0.01))
        min_confidence = float(request.form.get('min_confidence', 0.5))
        algorithm = request.form.get('algorithm', 'apriori')
        max_rules = request.form.get('max_rules', type=int, default=50)
        sort_by = request.form.get('sort_by', default='confidence')
        target_disease = request.form.get('target_disease', default='')
        
        ds = db.get_or_404(Dataset, dataset_id)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], ds.filename)
        
        try:
            # STEP 1-4: Preprocessing (Now returns transactions, shape, and class_col)
            transactions, shape, class_col = MiningEngine.preprocess_data(filepath, ds.file_type)
            
            # STEP 5-7: Execution
            params = {
                'min_support': min_support,
                'min_confidence': min_confidence,
                'algorithm': algorithm,
                'max_rules': max_rules,
                'sort_by': sort_by
            }
            # Target Disease filter is now integrated into class detection if target_disease is provided
            rules = MiningEngine.run_mining(transactions, params, class_col)
            
            # If user provided a target filter, we filter the rules at route level as well
            if target_disease:
                rules = [r for r in rules if target_disease.lower() in str(r['target_class']).lower()]

            if not rules:
                flash('Belgilangan parametrlar bilan hech qanday qoida topilmadi. Support (0.005-0.02) yoki Confidence (0.3-0.6) ko\'rsatkichlarini pasaytirib ko\'ring.', 'warning')
                return redirect(url_for('apriori.mine', dataset_id=dataset_id))
            
            # Generate AI Insights
            ai_insight = MiningEngine.get_ai_insights(rules)
            
            # Save analysis
            analysis = Analysis(
                dataset_id=ds.id,
                min_support=min_support,
                min_confidence=min_confidence,
                rules_count=len(rules),
                results_json=json.dumps(rules)
            )
            db.session.add(analysis)
            db.session.commit()
            
            # Unique target classes for filtering in UI
            target_classes = list(set([r['target_class'] for r in rules]))
            
            return render_template('apriori/results.html', 
                                   rules=rules, 
                                   dataset=ds, 
                                   analysis=analysis,
                                   insight=ai_insight,
                                   target_classes=target_classes)
            
        except Exception as e:
            # Professional Error System (Step 11)
            error_msg = f"Tahlil to'xtatildi: {str(e)}"
            flash(error_msg, 'danger')
            return redirect(url_for('apriori.mine', dataset_id=dataset_id))
            
    return render_template('apriori/mine.html', datasets=datasets, selected_ds=selected_dataset)

@apriori_bp.route('/history')
@login_required
def history():
    analyses = Analysis.query.join(Dataset).filter(Dataset.user_id == current_user.id).order_by(Analysis.created_at.desc()).all()
    return render_template('apriori/history.html', analyses=analyses)

@apriori_bp.route('/view_result/<int:id>')
@login_required
def view_result(id):
    analysis = db.session.get(Analysis, id)
    if not analysis:
        flash('Tahlil natijasi topilmadi.', 'danger')
        return redirect(url_for('analytics.index'))
    if analysis.dataset.user_id != current_user.id:
        flash('Ruxsat yo\'q', 'danger')
        return redirect(url_for('dashboard.home'))
    
    rules = json.loads(analysis.results_json)
    ai_insight = MiningEngine.get_ai_insights(rules)
    target_classes = list(set([r['target_class'] for r in rules]))
    
    return render_template('apriori/results.html', 
                           rules=rules, 
                           dataset=analysis.dataset, 
                           analysis=analysis,
                           insight=ai_insight,
                           target_classes=target_classes)

@apriori_bp.route('/export/<int:id>/<format>')
@login_required
def export_result(id, format):
    analysis = db.get_or_404(Analysis, id)
    if analysis.dataset.user_id != current_user.id:
        return "Unauthorized", 403
    
    rules = json.loads(analysis.results_json)
    
    if format == 'json':
        response = make_response(analysis.results_json)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=analysis_{id}.json'
        return response
    
    elif format == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Antecedents', 'Consequents', 'Support', 'Confidence', 'Lift', 'Strength'])
        for r in rules:
            writer.writerow([
                r['id'], 
                ", ".join(r['antecedents']), 
                ", ".join(r['consequents']), 
                r['support'], 
                r['confidence'], 
                r['lift'], 
                r['strength']
            ])
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=analysis_{id}.csv'
        return response
    
    return redirect(url_for('apriori.view_result', id=id))
