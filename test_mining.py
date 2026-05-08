from app.apriori.engine import MiningEngine
import logging

logging.basicConfig(level=logging.DEBUG)

filepath = 'test_medical.csv'
transactions, shape, class_col = MiningEngine.preprocess_data(filepath)
print(f"Transactions ({len(transactions)}):")
for t in transactions[:3]:
    print("  ", t)
print("Shape:", shape)
print("Class Col:", class_col)

params = {
    'min_support': 0.01,
    'min_confidence': 0.5,
    'max_rules': 50,
    'sort_by': 'confidence'
}

rules = MiningEngine.run_mining(transactions, params, class_col)
print(f"Rules found: {len(rules)}")
for r in rules[:2]:
    print(r)
