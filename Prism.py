from pandas.api.types import is_numeric_dtype
import pandas as pd
import argparse


class DatasetAnalyzer:
    """Analyzes any CSV dataset and generates a structured analysis report.

    Automatically detects column types (numeric continuous, categorical,
    temporal, identifier, or excluded) and computes appropriate descriptive
    statistics for each group. All summaries use lazy evaluation: computed
    once on first access and cached for subsequent calls.

    Attributes:
        DEFAULT_LOW_THRESHOLD (float): Default cardinality ratio threshold
            below which a numeric column is treated as categorical-encoded.
        DEFAULT_HIGH_THRESHOLD (float): Default cardinality ratio threshold
            above which a string column is treated as an identifier.

    Example:
        >>> analyzer = DatasetAnalyzer.from_csv('data/models.csv')
        >>> print(analyzer.generate_report())

        >>> # With custom thresholds
        >>> analyzer = DatasetAnalyzer.from_csv('data/models.csv', low_threshold=0.1)
        >>> print(analyzer.generate_report())
    """

    DEFAULT_LOW_THRESHOLD: float = 0.05
    DEFAULT_HIGH_THRESHOLD: float = 0.5

    def __init__(
        self,
        df: pd.DataFrame,
        low_threshold: float = DEFAULT_LOW_THRESHOLD,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
    ) -> None:
        """Initializes DatasetAnalyzer with a DataFrame and optional thresholds.

        Args:
            df (pd.DataFrame): The dataset to analyze.
            low_threshold (float): Cardinality ratio below which a numeric
                column is treated as categorical. Defaults to 0.05.
            high_threshold (float): Cardinality ratio above which a string
                column is treated as an identifier. Defaults to 0.5.
        """
        self._df = df
        self._low_threshold = low_threshold
        self._high_threshold = high_threshold
        self._classification: dict | None = None
        self._numeric_summary: dict | None = None
        self._categorical_summary: dict | None = None
        self._temporal_summary: dict | None = None
        self._report: str | None = None

    @classmethod
    def from_csv(
        cls,
        path: str,
        low_threshold: float = DEFAULT_LOW_THRESHOLD,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
    ) -> "DatasetAnalyzer":
        """Alternative constructor that loads a dataset directly from a CSV file.

        Args:
            path (str): Path to the CSV file on disk.
            low_threshold (float): Cardinality ratio threshold for numeric
                column detection. Defaults to 0.05.
            high_threshold (float): Cardinality ratio threshold for identifier
                column detection. Defaults to 0.5.

        Returns:
            DatasetAnalyzer: A new instance initialized with the loaded DataFrame.
        """
        df = pd.read_csv(path)
        return cls(df, low_threshold, high_threshold)

    def classify_columns(self) -> dict[str, str]:
        """Classifies each DataFrame column into a detected type.

        Uses lazy evaluation: classification is computed on first call
        and cached for all subsequent calls.

        Types returned:
            - 'numeric_continuous': numeric column with high cardinality.
            - 'categorical': low-cardinality numeric or string column.
            - 'temporal': string column parsable as datetime.
            - 'identifier': high-cardinality string column (e.g. URLs, IDs).
            - 'excluded_all_nan': column with no valid values.

        Returns:
            dict[str, str]: Mapping of column name to its detected type.
        """
        if self._classification is None:
            self._classification = self._compute_classification()
        return self._classification

    def get_numeric_summary(self) -> dict[str, dict]:
        """Returns descriptive statistics for all numeric continuous columns.

        Computes min, max, mean, median, standard deviation, and missing
        value count. Uses lazy evaluation: computed once and cached.

        Returns:
            dict[str, dict]: Mapping of column name to a statistics dict
                with keys: 'min', 'max', 'mean', 'median', 'std', 'missing'.
        """
        if self._numeric_summary is None:
            classification = self.classify_columns()
            cols = [k for k, v in classification.items() if v == 'numeric_continuous']
            self._numeric_summary = self._compute_numeric_summary(cols)
        return self._numeric_summary

    def get_categorical_summary(self) -> dict[str, dict]:
        """Returns frequency statistics for all categorical columns.

        Computes unique value count, top 5 most frequent values, and missing
        value count. Uses lazy evaluation: computed once and cached.

        Returns:
            dict[str, dict]: Mapping of column name to a statistics dict
                with keys: 'unique_values', 'top_5', 'missing'.
        """
        if self._categorical_summary is None:
            classification = self.classify_columns()
            cols = [k for k, v in classification.items() if v == 'categorical']
            self._categorical_summary = self._compute_categorical_summary(cols)
        return self._categorical_summary

    def get_temporal_summary(self) -> dict[str, dict]:
        """Returns time-range statistics for all temporal columns.

        Computes earliest date, latest date, total range in days, and missing
        value count. Uses lazy evaluation: computed once and cached.

        Returns:
            dict[str, dict]: Mapping of column name to a statistics dict
                with keys: 'min', 'max', 'range_days', 'missing'.
        """
        if self._temporal_summary is None:
            classification = self.classify_columns()
            cols = [k for k, v in classification.items() if v == 'temporal']
            self._temporal_summary = self._compute_temporal_summary(cols)
        return self._temporal_summary

    def _compute_classification(self) -> dict[str, str]:
        """Implements the column type detection algorithm.

        Applies the following detection logic in order for each column:
            0. 100% NaN values -> 'excluded_all_nan'
            1. bool dtype -> 'categorical'
            2. numeric + cardinality ratio > low_threshold -> 'numeric_continuous'
            3. numeric + cardinality ratio <= low_threshold -> 'categorical'
            4. string parsable as datetime (success ratio > 0.9) -> 'temporal'
            5. string + cardinality ratio > high_threshold -> 'identifier'
            6. string + cardinality ratio <= high_threshold -> 'categorical'

        Cardinality ratio is computed as nunique() / len(dropna()) to avoid
        distortion from missing values.

        Returns:
            dict[str, str]: Mapping of column name to its detected type.
        """
        result: dict[str, str] = {}

        for col in self._df:
            series = self._df[col]

            if series.isna().sum() == len(series):
                result[col] = 'excluded_all_nan'

            elif series.dtype == bool:
                result[col] = 'categorical'

            elif is_numeric_dtype(series):
                cardinality_ratio = series.nunique() / len(series.dropna())
                if cardinality_ratio > self._low_threshold:
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
                    if cardinality_ratio > self._high_threshold:
                        result[col] = 'identifier'
                    else:
                        result[col] = 'categorical'

        return result

    def _compute_numeric_summary(self, cols: list[str]) -> dict[str, dict]:
        """Computes descriptive statistics for a list of numeric columns.

        NaN values are automatically excluded by pandas from all calculations.

        Args:
            cols (list[str]): Names of columns to analyze.

        Returns:
            dict[str, dict]: Mapping of column name to a statistics dict
                with keys: 'min', 'max', 'mean', 'median', 'std', 'missing'.
                All values are native Python floats or ints.
        """
        result: dict[str, dict] = {}

        for col in cols:
            series = self._df[col]
            result[col] = {
                'min': float(series.min()),
                'max': float(series.max()),
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'missing': int(series.isnull().sum()),
            }

        return result

    def _compute_categorical_summary(self, cols: list[str]) -> dict[str, dict]:
        """Computes frequency statistics for a list of categorical columns.

        Args:
            cols (list[str]): Names of columns to analyze.

        Returns:
            dict[str, dict]: Mapping of column name to a statistics dict
                with keys: 'unique_values' (int), 'top_5' (dict of value
                to count), 'missing' (int).
        """
        result: dict[str, dict] = {}

        for col in cols:
            series = self._df[col]
            result[col] = {
                'unique_values': int(series.nunique()),
                'top_5': series.value_counts().head(5).to_dict(),
                'missing': int(series.isnull().sum()),
            }

        return result

    def _compute_temporal_summary(self, cols: list[str]) -> dict[str, dict]:
        """Computes time-range statistics for a list of temporal columns.

        String columns are parsed using pd.to_datetime. 
        Unparsable values become NaT and are excluded.

        Args:
            cols (list[str]): Names of columns to analyze.

        Returns:
            dict[str, dict]: Mapping of column name to a statistics dict
                with keys: 'min' (Timestamp), 'max' (Timestamp),
                'range_days' (int), 'missing' (int).
        """
        result: dict[str, dict] = {}

        for col in cols:

            series = self._df[col]
            parsed = pd.to_datetime(series, errors='coerce')
            valid = parsed.notna()

            if valid.any():
                result[col] = {
                    'min': parsed.min(),
                    'max': parsed.max(),
                    'range_days': (parsed.max() - parsed.min()).days,
                    'missing': int(parsed.isnull().sum()),
                }
            else:
                result[col] = {
                    'min': None,
                    'max': None,
                    'range_days': None,
                    'missing': int(parsed.isnull().sum()),
                }

        return result

    def generate_report(self) -> str:
        """Generates a formatted analysis report for the entire dataset.

        Orchestrates all summary methods and formats their output into a
        human-readable string with clearly separated sections for each
        column type. Excluded and identifier columns are listed at the end.

        Returns:
            str: The complete formatted report, ready to print or save to file.
        """

        if self._report is not None:
            return self._report
        
        lines: list[str] = []
        classification = self.classify_columns()

        numeric_summary = self.get_numeric_summary()
        df_numeric = pd.DataFrame(numeric_summary).T
        df_numeric['missing'] = df_numeric['missing'].astype(int)

        categorical_summary = self.get_categorical_summary()

        temporal_summary = self.get_temporal_summary()
        df_temporal = pd.DataFrame(temporal_summary).T

        lines.append("/----------------------------------------- PRISM REPORT ------------------------------------------/")
        lines.append(f"Dataset shape: {self._df.shape}")
        lines.append("")
        lines.append("/--------------------------------------- NUMERIC SUMMARY ----------------------------------------/")
        lines.append(df_numeric.to_string())
        lines.append("")
        lines.append("/------------------------------------- CATEGORICAL SUMMARY --------------------------------------/")
        for col, stats in categorical_summary.items():
            lines.append(f"{col} (unique: {stats['unique_values']}, missing: {stats['missing']})")
            for k, v in stats['top_5'].items():
                lines.append(f"  {k} : {v}")
        lines.append("")
        lines.append("/--------------------------------------- TEMPORAL SUMMARY ---------------------------------------/")
        lines.append(df_temporal.to_string())
        lines.append("")
        lines.append(f"Excluded NaN: {[k for k, v in classification.items() if v == 'excluded_all_nan']}")
        lines.append(f"Identifier:   {[k for k, v in classification.items() if v == 'identifier']}")

        self._report = '\n'.join(lines)
        return self._report

def main() -> None:
    """Entry point for the Prism command-line interface.

    Parses the CSV file path and optional threshold arguments, initializes
    a DatasetAnalyzer, and prints the generated report to stdout.

    Example:
        $ python Prism.py data/models.csv
        $ python Prism.py data/models.csv --low 0.1 --high 0.7
    """
    parser = argparse.ArgumentParser(
        description="Prism - Automatic Dataset Analyzer. Pass a CSV file to generate a full analysis report."
    )
    parser.add_argument(
        'path',
        help='Path to the CSV file to analyze.',
    )
    parser.add_argument(
        '--low',
        help=f'Cardinality ratio threshold for numeric column detection. Default: {DatasetAnalyzer.DEFAULT_LOW_THRESHOLD}',
        type=float,
        default=DatasetAnalyzer.DEFAULT_LOW_THRESHOLD,
    )
    parser.add_argument(
        '--high',
        help=f'Cardinality ratio threshold for identifier column detection. Default: {DatasetAnalyzer.DEFAULT_HIGH_THRESHOLD}',
        type=float,
        default=DatasetAnalyzer.DEFAULT_HIGH_THRESHOLD,
    )

    args = parser.parse_args()
    analyzer = DatasetAnalyzer.from_csv(args.path, args.low, args.high)
    print(analyzer.generate_report())


if __name__ == "__main__":
    main()