from flask import Blueprint, render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from models.user import User, Dataset, Analysis
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def check_admin():
    if current_user.role != 'Admin':
        abort(403)

@admin_bp.route('/')
def index():
    users = User.query.all()
    datasets = Dataset.query.all()
    analyses = Analysis.query.all()
    return render_template('admin/index.html', users=users, datasets=datasets, analyses=analyses)

@admin_bp.route('/user/delete/<int:id>')
def delete_user(id):
    if current_user.id == id:
        flash('O\'zingizni o\'chira olmaysiz', 'danger')
        return redirect(url_for('admin.index'))
    
    user = db.session.get(User, id)
    if not user:
        flash('Foydalanuvchi topilmadi.', 'danger')
        return redirect(url_for('admin.index'))
        
    db.session.delete(user)
    db.session.commit()
    flash('Foydalanuvchi o\'chirildi', 'info')
    return redirect(url_for('admin.index'))

@admin_bp.route('/user/role/<int:id>/<role>')
def change_role(id, role):
    user = db.session.get(User, id)
    if not user:
        flash('Foydalanuvchi topilmadi.', 'danger')
        return redirect(url_for('admin.index'))
        
    if role in ['Admin', 'Researcher', 'User']:
        user.role = role
        db.session.commit()
        flash(f'Rol {role} ga o\'zgartirildi', 'success')
    return redirect(url_for('admin.index'))
