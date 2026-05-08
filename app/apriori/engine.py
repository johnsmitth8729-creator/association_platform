import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
import json
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MiningEngine:
    @staticmethod
    def preprocess_data(filepath, file_type='csv'):
        try:
            # STEP 1: Smart delimiter and encoding detection
            import csv
            with open(filepath, 'rb') as f:
                raw_data = f.read(15000)
                import charset_normalizer
                detected = charset_normalizer.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'

            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                sample = f.read(15000)
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample)
                    delimiter = dialect.delimiter
                except:
                    delimiter = ';' if ';' in sample else ','
            
            df = pd.read_csv(filepath, sep=delimiter, on_bad_lines='skip', engine='python', encoding=encoding)
            df.columns = [str(c).strip() for c in df.columns]
            
            # STEP 2: Intelligent Metadata Filtering (More specific patterns)
            meta_patterns = ['id', 'name', 'ism', 'familiya', 'fio', 'passport', 'phone', 'tel', 'bemor', 't/r', 'index']
            cols_to_drop = []
            for col in df.columns[:-1]: 
                c_low = col.lower().strip()
                # Drop if matches meta patterns or is 100% unique (likely an ID)
                if any(p == c_low or c_low.startswith(p + '_') or c_low.endswith('_' + p) for p in meta_patterns) or df[col].nunique() == len(df):
                    cols_to_drop.append(col)
            
            logger.info(f"Dropping columns: {cols_to_drop}")
            df = df.drop(columns=cols_to_drop)
            
            # STEP 3: Stability Guard
            if len(df.columns) > 30:
                df = df.iloc[:, list(range(29)) + [-1]]

            # STEP 4: Professional Numeric Binning (Majburiy Range)
            for col in df.columns[:-1]:
                try:
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    if numeric_series.notnull().sum() > len(df) * 0.4:
                        if 'yosh' in col.lower() or 'age' in col.lower():
                            # 45 -> Yoshi_40_50
                            start = (numeric_series // 10 * 10).fillna(0).astype(int)
                            end = start + 10
                            df[col] = [f"{s}_{e}" for s, e in zip(start, end)]
                        elif numeric_series.nunique() > 5:
                            # Generic binning
                            df[col] = pd.qcut(numeric_series, q=3, labels=['Past', 'O\'rta', 'Yuqori'], duplicates='drop').astype(str)
                        else:
                            df[col] = df[col].astype(str).str.strip()
                    else:
                        df[col] = df[col].astype(str).str.strip()
                except:
                    df[col] = df[col].astype(str).str.strip()

            # STEP 5: Universal Transaction Generation (Column_Value Format)
            class_col = df.columns[-1]
            transactions = []
            for _, row in df.iterrows():
                transaction = []
                for col in df.columns[:-1]:
                    val = str(row[col]).strip()
                    if val and val.lower() != 'nan' and val != '':
                        transaction.append(f"{col}_{val}")
                
                target_val = str(row[class_col]).strip()
                if target_val and target_val.lower() != 'nan':
                    transaction.append(f"{class_col}_{target_val}")
                
                if transaction:
                    transactions.append(transaction)
            
            return transactions, df.shape, class_col
        except Exception as e:
            logger.error(f"Preprocess Error: {str(e)}\n{traceback.format_exc()}")
            raise Exception(f"Ma'lumotlarni tahlil qilishda xato: {str(e)}")

    @staticmethod
    def run_mining(transactions, params, target_class_name):
        try:
            # STEP 6: Professional Auto-Tuning for Support
            row_count = len(transactions)
            if row_count < 50:
                default_support = 0.15
            elif row_count < 200:
                default_support = 0.1
            elif row_count < 1000:
                default_support = 0.05
            else:
                default_support = 0.01

            min_support = params.get('min_support', default_support)
            min_confidence = params.get('min_confidence', 0.4)
            max_rules = params.get('max_rules', 50)
            
            # Ensure safety floor (at least 2 occurrences for reliable rules, but allow 1 if support is extremely low)
            min_support = max(min_support, 1.1 / row_count) if row_count > 0 else 0.1
            
            logger.info(f"Running mining with Support: {min_support}, Confidence: {min_confidence}, Row Count: {row_count}")

            te = TransactionEncoder()
            te_ary = te.fit(transactions).transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

            # Use fpgrowth for speed
            frequent_itemsets = fpgrowth(df_encoded, min_support=min_support, use_colnames=True, max_len=4)
            
            if frequent_itemsets.empty:
                return []

            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
            
            if rules.empty:
                return []

            # STEP 10: Target-Prefix Filtering (Majburiy Class Rules)
            target_prefix = f"{target_class_name}_"
            
            # Filter: Consequent must contain target class prefix
            rules = rules[rules['consequents'].apply(lambda x: any(target_prefix in str(item) for item in x))]
            # Filter: Antecedent must NOT contain target class prefix
            rules = rules[rules['antecedents'].apply(lambda x: not any(target_prefix in str(item) for item in x))]
            
            sort_metric = params.get('sort_by', 'lift')
            if sort_metric not in rules.columns: sort_metric = 'confidence'
            
            rules = rules.sort_values(by=[sort_metric, 'confidence'], ascending=False).head(max_rules)
            
            rules_list = []
            for _, row in rules.iterrows():
                # Clean up formatting: Column_Value -> Column = Value
                ant = [str(a).replace('_', ': ', 1) if '_' in str(a) else str(a) for a in row['antecedents']]
                # Extract clean target class
                raw_con = [str(c) for c in row['consequents'] if target_prefix in str(c)]
                if not raw_con: continue
                
                clean_target = raw_con[0].replace(target_prefix, '')

                rules_list.append({
                    'id': len(rules_list) + 1,
                    'antecedents': ant,
                    'consequents': [clean_target],
                    'target_class': clean_target,
                    'target_name': target_class_name,
                    'support': float(row['support']),
                    'confidence': float(row['confidence']),
                    'lift': float(row['lift']),
                    'strength': 'Very Strong' if row['confidence'] >= 0.8 else 'Strong' if row['confidence'] >= 0.6 else 'Medium'
                })
                
            return rules_list
        except Exception as e:
            logger.error(f"Mining Error: {str(e)}\n{traceback.format_exc()}")
            return []

    @staticmethod
    def get_ai_insights(rules):
        if not rules:
            return "Ma'lumotlar orasida kuchli bog'liqliklar topilmadi. Dataset juda kichik bo'lishi mumkin. Iltimos, Support yoki Confidence ko'rsatkichlarini pasaytirib ko'ring."
        
        top_rule = rules[0]
        ant_text = " va ".join([a for a in top_rule['antecedents']])
        
        insight = f"Tizim asosiy qonuniyatni aniqladi: Agar bemorda **{ant_text}** holatlari kuzatilsa, "
        insight += f"unda **{top_rule['target_class']}** ehtimoli **{top_rule['confidence']*100:.1f}%** ni tashkil etadi. "
        insight += f"Ushbu bog'liqlik ishonchliligi (Confidence) juda yuqori."
        
        return insight
