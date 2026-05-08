import os
import pandas as pd
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models.user import Dataset
from datetime import datetime

dataset_bp = Blueprint('dataset', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dataset_bp.route('/list')
@login_required
def list_datasets():
    datasets = Dataset.query.filter_by(user_id=current_user.id).order_by(Dataset.created_at.desc()).all()
    return render_template('dataset/list.html', datasets=datasets)

@dataset_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Fayl tanlanmagan', 'warning')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Fayl nomi bo\'sh', 'warning')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().timestamp()}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Basic analysis using Pandas
            file_ext = filename.rsplit('.', 1)[1].lower()
            try:
                if file_ext == 'csv':
                    df = pd.read_csv(filepath)
                elif file_ext == 'xlsx':
                    df = pd.read_excel(filepath)
                else: # txt
                    df = pd.read_csv(filepath, sep='\t')
                
                rows, cols = df.shape
                
                new_ds = Dataset(
                    filename=unique_filename,
                    original_name=filename,
                    file_type=file_ext,
                    row_count=rows,
                    col_count=cols,
                    user_id=current_user.id
                )
                db.session.add(new_ds)
                db.session.commit()
                
                flash(f'Dataset muvaffaqiyatli yuklandi: {rows} qator, {cols} ustun.', 'success')
                return redirect(url_for('dataset.list_datasets'))
                
            except Exception as e:
                flash(f'Faylni o\'qishda xatolik: {str(e)}', 'danger')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)
        else:
            flash('Ruxsat berilmagan fayl turi', 'danger')
            
    return render_template('dataset/upload.html')

@dataset_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    ds = db.session.get(Dataset, id)
    if not ds:
        flash('Dataset topilmadi.', 'danger')
        return redirect(url_for('dataset.list_datasets'))
    if ds.user_id != current_user.id:
        flash('Ruxsat yo\'q', 'danger')
        return redirect(url_for('dataset.list_datasets'))
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], ds.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        
    db.session.delete(ds)
    db.session.commit()
    flash('Dataset o\'chirildi', 'info')
    return redirect(url_for('dataset.list_datasets'))
