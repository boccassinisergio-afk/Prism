# Prism
### Pandas Report & Intelligent Summary Maker

> *A prism splits white light into its component wavelengths.*
> *Prism splits any CSV dataset into its component column types and surfaces what matters.*

Prism is a Python tool that accepts any CSV file and automatically generates a structured analysis report - detecting column types, computing appropriate statistics for each group, and presenting results in a clean, readable format.

Built as a real-world application of object-oriented programming and pandas, not as a textbook exercise.

---

## What it does

Point Prism at any CSV. It will:

1. **Classify every column** into one of five types: numeric continuous, categorical, temporal, identifier, or excluded (100% NaN).
2. **Apply the right analysis** to each type: descriptive statistics for numerics, frequency tables for categoricals, date ranges for temporals.
3. **Generate a formatted report** with clearly separated sections, ready to read or pipe into a file.

```
$ python Prism.py data/llm_models.csv
```

```
/----------------------------------------- PRISM REPORT ------------------------------------------/
Dataset shape: (1004, 11)

/--------------------------------------- NUMERIC SUMMARY ----------------------------------------/
                        min           max          mean       median           std  missing
parameters             16.0  3.000000e+12  7.307195e+10  375000000.0  2.593737e+11      309
training_compute_flop  40.0  5.000000e+26  3.773911e+24    8.300e+20  3.184713e+25      483

/------------------------------------- CATEGORICAL SUMMARY --------------------------------------/
organization (unique: 434, missing: 18)
  OpenAI : 59
  Google : 54
  Google DeepMind : 38
  DeepMind : 30
  Meta AI : 28

domain (unique: 80, missing: 2)
  Language : 374
  Vision : 201
  Games : 47
  Biology : 42
  Image generation : 39

/--------------------------------------- TEMPORAL SUMMARY ---------------------------------------/
              min                  max  range_days  missing
release_date  1950-07-02  2026-03-11       27646        4

Excluded NaN: ['model_name', 'training_dataset_size', 'training_cost_usd']
Identifier:   ['link']
```

---

## Design decisions worth reading

### Automatic column type detection

The core algorithm goes beyond pandas dtypes. A column of integers might be a salary (numeric continuous) or an experience level code (categorical). Prism resolves this ambiguity using a **cardinality ratio**: the number of unique values divided by the number of non-null rows.

```
cardinality_ratio = series.nunique() / len(series.dropna())
```

- Ratio above `low_threshold` (default 0.05) and numeric dtype: continuous variable, compute mean/std/percentiles.
- Ratio below `low_threshold` and numeric dtype: categorical-encoded, compute value counts.
- String column parsable as datetime (success ratio above 90%): temporal, compute min/max/range.
- String column with ratio above `high_threshold` (default 0.5): identifier (URL, ID), listed but not analyzed.

Both thresholds are configurable at instantiation or via CLI flags.

### Lazy evaluation with memoization

No computation happens at instantiation. Every summary is calculated only when requested, and cached after the first call. Calling `generate_report()` ten times costs the same as calling it once.

```python
def classify_columns(self) -> dict[str, str]:
    if self._classification is None:
        self._classification = self._compute_classification()
    return self._classification
```

### Alternative constructor pattern

Prism accepts a pre-loaded DataFrame directly (useful in notebooks or testing) or a file path via the `from_csv()` class method. The public interface works the same either way.

```python
# From a file
analyzer = DatasetAnalyzer.from_csv('data/models.csv')

# From an existing DataFrame
analyzer = DatasetAnalyzer(df)

# With custom thresholds
analyzer = DatasetAnalyzer.from_csv('data/models.csv', low_threshold=0.1, high_threshold=0.7)
```

### Private/public separation

Public methods handle caching and orchestration. Private `_compute_*` methods do pure calculation with no side effects. This separation makes each method independently testable and keeps the public API clean.

---

## Installation

```bash
git clone https://github.com/boccassinisergio-afk/Prism.git
cd Prism
uv venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

**Requirements:** Python 3.10+, pandas

---

## Usage

### Quick start - Jupyter notebook
Open `notebook/Prism_notebook.ipynb` for an interactive demo
running on the included LLM dataset.

### As a CLI tool

```bash
# Basic usage
python Prism.py path/to/file.csv

# Custom thresholds
python Prism.py path/to/file.csv --low 0.1 --high 0.7

# Save report to file
python Prism.py path/to/file.csv > report.txt
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `path` | positional | required | Path to the CSV file |
| `--low` | float | 0.05 | Threshold for numeric vs categorical detection |
| `--high` | float | 0.5 | Threshold for identifier vs categorical detection |

### As a library

```python
from Prism import DatasetAnalyzer

# From CSV
analyzer = DatasetAnalyzer.from_csv('data/models.csv')

# From existing DataFrame
analyzer = DatasetAnalyzer(df)

# Individual summaries
print(analyzer.classify_columns())
print(analyzer.get_numeric_summary())
print(analyzer.get_categorical_summary())
print(analyzer.get_temporal_summary())

# Full report
print(analyzer.generate_report())
```

---

## Tested on

LLM Performance and Evaluation Dataset (Kaggle) - 1,004 rows, 11 columns including:
- Float columns with 30-48% missing values (real-world sparsity)
- Date strings requiring runtime parsing (`pd.to_datetime`)
- Categoricals ranging from 1 unique value (`source`) to 434 (`organization`)
- Three fully empty columns (100% NaN)
- One identifier column (`link`)

The dataset exercises every branch of the detection algorithm.

---

## Technical stack

| Tool | Role |
|---|---|
| Python 3.10+ | Core language |
| pandas | Data loading, analysis, display formatting |
| argparse | CLI interface |
| uv | Package management |

Full type hints and Google-style docstrings throughout.

---

## Project context

Prism is part of a portfolio built during a career transition into AI and software development, alongside:

- [Pulsar](https://github.com/boccassinisergio-afk/PULSAR) - output tracker with data-driven regex engine and OOP architecture
- [Synapse](https://github.com/boccassinisergio-afk/Synapse) - concept tracker, paired with Pulsar as an emit/absorb suite

---

## Author

**Sergio Boccassini**
[GitHub](https://github.com/boccassinisergio-afk) - [LinkedIn](https://linkedin.com/in/sergio-boccassini) - [X](https://x.com/boccassini_ai)