from app import create_app, db
from app.apriori.engine import MiningEngine
import os

app = create_app()
with app.app_context():
    from models.user import Dataset
    ds = db.session.get(Dataset, 8)
    if not ds:
        print("Dataset 8 not found, picking first dataset")
        ds = Dataset.query.first()
        
    print(f"Using dataset: {ds.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], ds.filename)
    transactions, shape, class_col = MiningEngine.preprocess_data(filepath, ds.file_type)
    
    params = {
        'min_support': 0.01,
        'min_confidence': 0.5,
        'algorithm': 'apriori',
        'max_rules': 50,
        'sort_by': 'confidence'
    }
    
    rules = MiningEngine.run_mining(transactions, params, class_col)
    print("Rules count before target_disease filter:", len(rules))
    
    target_disease = ''
    if target_disease:
        rules = [r for r in rules if target_disease.lower() in str(r['target_class']).lower()]
    
    print("Rules count after target_disease filter:", len(rules))
