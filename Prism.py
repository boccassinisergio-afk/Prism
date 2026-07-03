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

    def get_numeric_summary(self):
        # lazy + memoization, chiama classify_columns internamente

    def get_categorical_summary(self):
        # idem

    def get_temporal_summary(self):
        # idem

    def generate_report(self):
        # orchestratore

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

