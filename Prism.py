from unittest import result
from pandas.api.types import is_numeric_dtype

import pandas as pd
from pandas import col

class DatasetAnalyzer():
    def __init__(self, df: pd.DataFrame):
        self._df = df
        self._classification = None
        self._numeric_summary = None
        self._categorical_summary = None
        self._temporal_summary = None
        self._report = None

    @classmethod
    def from_csv(cls, path: str) -> 'DatasetAnalyzer':
        df = pd.read_csv(path)
        return cls(df)

    def classify_columns(self) -> dict:
        # lazy + memoization, ritorna dict {colonna: trattamento}
        if self._classification is None:
            self._classification = self._compute_classification()
        return self._classification


    def get_numeric_summary(self):
        # lazy + memoization, chiama classify_columns internamente
        if self._numeric_summary is None:
            classification = self.classify_columns()
            cols = [k for k, v in classification.items() if v == 'numeric_continuous']
            self._numeric_summary = self._compute_numeric_summary(cols)
        return self._numeric_summary

    def get_categorical_summary(self):
        # idem
        if self._categorical_summary is None:
            classification = self.classify_columns()
            cols = [k for k, v in classification.items() if v == 'categorical']
            self._categorical_summary = self._compute_categorical_summary(cols)
        return self._categorical_summary
    
    def get_temporal_summary(self):
        # idem
        if self._temporal_summary is None:
            classification = self.classify_columns()
            cols = [k for k, v in classification.items() if v == 'temporal']
            self._temporal_summary = self._compute_temporal_summary(cols)
        return self._temporal_summary

    def _compute_classification(self):
        result = {}
        LOW_THRESHOLD = 0.05
        HIGH_THRESHOLD = 0.5
        for col in self._df:
            series = self._df[col]
            if series.isna().sum() == len(series):    
                result[col] = 'excluded_all_nan' 
            elif series.dtype == bool:
                result[col] = 'categorical'
            elif is_numeric_dtype(series):
                cardinality_ratio = series.nunique() / len(series.dropna())
                if cardinality_ratio > LOW_THRESHOLD:
                    result[col] = 'numeric_continuous'
                else:
                    result[col] = 'categorical'
            else:
                parsed = pd.to_datetime(series, errors='coerce')
                temporal_ratio = parsed.notna().sum() / series.notna().sum()

                if temporal_ratio > 0.9:
                    result[col] = 'temporal'
                else:
                    cardinality_ratio = series.nunique() / len(series.dropna())
                    if cardinality_ratio > HIGH_THRESHOLD:
                        result[col] = 'identifier'
                    else:
                        result[col] = 'categorical'
        return result

    def _compute_numeric_summary(self, cols):
        # calcolo puro
        result = {}

        for col in cols:
            series = self._df[col]
            result[col] = {
                'min': float(series.min()),
                'max': float(series.max()),
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'missing': int(series.isnull().sum())
            }

        return result

    def _compute_categorical_summary(self, cols):
        # calcolo puro
        result = {}

        for col in cols:
            series = self._df[col]
            result[col] = {
                'unique_values': series.nunique(),
                'top_5': series.value_counts().head(5).to_dict(),
                'missing': int(series.isnull().sum())
            }
        
        return result

    def _compute_temporal_summary(self, cols):
        # calcolo puro
        result = {}

        for col in cols:
            series = self._df[col]
            parsed = pd.to_datetime(series, errors='coerce')
            result[col] = {
                'min': parsed.min(),
                'max': parsed.max(),
                'range_days': (parsed.max() - parsed.min()).days,
                'missing': int(parsed.isnull().sum())
            }
        
        return result

    def generate_report(self):

        lines = []
        classification = self.classify_columns()

        numeric_summary = self.get_numeric_summary()
        categorical_summary = self.get_categorical_summary()
        temporal_summary = self.get_temporal_summary()

        lines.append('=== Prism report ===')
        lines.append(f"Dataset shape: {self._df.shape}")
        lines.append(f"Numeric summary: {numeric_summary}")
        lines.append(f"Categorical summary: {categorical_summary}")
        lines.append(f"Temporal summary: {temporal_summary}")
        lines.append(f"Excluded NaN: {[k for k, v in classification.items() if v == 'excluded_all_nan']}")
        lines.append(f"Identifier: {[k for k, v in classification.items() if v == 'identifier']}")

        return '\n'.join(lines)


def main():
    df = pd.read_csv("data/llm_benchmarks_2026.csv")
    print(df.info())
    print(df.shape)
    print(df.isna().sum())
    print(df.head())

    df = pd.read_csv('data.csv')
    analyzer = DatasetAnalyzer(df) #case: hai gia un dataframe, dopo verifichiamo i metodi di input

    analyzer = DatasetAnalyzer('data.csv') #case: se vuoi partire da csv, dopo verifichiamo i metodi di input

main()
