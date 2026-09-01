# Prism
### Generatore di Report Pandas e Riepiloghi Intelligenti

**🇮🇹 Italiano | [🇬🇧 English](#english)**

> *Un prisma scompone la luce bianca nelle sue lunghezze d'onda componenti.*
> *Prism scompone qualsiasi dataset CSV nei suoi tipi di colonna componenti e fa emergere ciò che conta.*

Prism è un tool Python che accetta qualsiasi file CSV e genera automaticamente un report di analisi strutturato - rilevando i tipi di colonna, calcolando le statistiche appropriate per ogni gruppo e presentando i risultati in un formato pulito e leggibile.

Costruito come applicazione reale di programmazione orientata agli oggetti e pandas, non come esercizio da manuale.

---

## Cosa fa

Punta Prism su qualsiasi CSV. Il tool:

1. **Classifica ogni colonna** in uno di cinque tipi: numerica continua, categorica, temporale, identificatore, o esclusa (100% NaN).
2. **Applica l'analisi corretta** a ogni tipo: statistiche descrittive per le numeriche, tabelle di frequenza per le categoriche, intervalli di date per le temporali.
3. **Genera un report formattato** con sezioni chiaramente separate, pronto da leggere o da reindirizzare su file.

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

## Scelte di design che vale la pena leggere

### Rilevamento automatico del tipo di colonna

L'algoritmo di base va oltre i dtype di pandas. Una colonna di interi potrebbe essere uno stipendio (numerica continua) o un codice di livello di esperienza (categorica). Prism risolve questa ambiguità usando un **rapporto di cardinalità**: il numero di valori unici diviso per il numero di righe non nulle.

```
cardinality_ratio = series.nunique() / len(series.dropna())
```

- Rapporto sopra `low_threshold` (default 0.05) e dtype numerico: variabile continua, calcola media/std/percentili.
- Rapporto sotto `low_threshold` e dtype numerico: codificata come categorica, calcola i conteggi dei valori.
- Colonna stringa interpretabile come datetime (tasso di successo sopra il 90%): temporale, calcola min/max/intervallo.
- Colonna stringa con rapporto sopra `high_threshold` (default 0.5): identificatore (URL, ID), elencata ma non analizzata.

Entrambe le soglie sono configurabili all'istanziazione o tramite flag CLI.

### Valutazione lazy con memoization

Nessun calcolo avviene all'istanziazione. Ogni riepilogo viene calcolato solo quando richiesto, e messo in cache dopo la prima chiamata. Chiamare `generate_report()` dieci volte costa quanto chiamarlo una sola volta.

```python
def classify_columns(self) -> dict[str, str]:
    if self._classification is None:
        self._classification = self._compute_classification()
    return self._classification
```

### Pattern del costruttore alternativo

Prism accetta direttamente un DataFrame già caricato (utile in notebook o test) oppure un percorso file tramite il metodo di classe `from_csv()`. L'interfaccia pubblica funziona allo stesso modo in entrambi i casi.

```python
# Da un file
analyzer = DatasetAnalyzer.from_csv('data/models.csv')

# Da un DataFrame esistente
analyzer = DatasetAnalyzer(df)

# Con soglie personalizzate
analyzer = DatasetAnalyzer.from_csv('data/models.csv', low_threshold=0.1, high_threshold=0.7)
```

### Separazione privato/pubblico

I metodi pubblici gestiscono caching e orchestrazione. I metodi privati `_compute_*` eseguono calcolo puro senza effetti collaterali. Questa separazione rende ogni metodo testabile in modo indipendente e mantiene pulita l'API pubblica.

---

## Installazione

```bash
git clone https://github.com/boccassinisergio-afk/Prism.git
cd Prism
uv venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

**Requisiti:** Python 3.10+, pandas

---

## Utilizzo

### Avvio rapido - notebook Jupyter
Apri `notebook/Prism_notebook.ipynb` per una demo interattiva
sul dataset LLM incluso.

### Come tool CLI

```bash
# Utilizzo base
python Prism.py path/to/file.csv

# Soglie personalizzate
python Prism.py path/to/file.csv --low 0.1 --high 0.7

# Salva il report su file
python Prism.py path/to/file.csv > report.txt
```

| Argomento | Tipo | Default | Descrizione |
|---|---|---|---|
| `path` | posizionale | richiesto | Percorso del file CSV |
| `--low` | float | 0.05 | Soglia per il rilevamento numerica vs categorica |
| `--high` | float | 0.5 | Soglia per il rilevamento identificatore vs categorica |

### Come libreria

```python
from Prism import DatasetAnalyzer

# Da CSV
analyzer = DatasetAnalyzer.from_csv('data/models.csv')

# Da DataFrame esistente
analyzer = DatasetAnalyzer(df)

# Riepiloghi individuali
print(analyzer.classify_columns())
print(analyzer.get_numeric_summary())
print(analyzer.get_categorical_summary())
print(analyzer.get_temporal_summary())

# Report completo
print(analyzer.generate_report())
```

---

## Testato su

LLM Performance and Evaluation Dataset (Kaggle) - 1.004 righe, 11 colonne tra cui:
- Colonne float con il 30-48% di valori mancanti (sparsità reale)
- Stringhe di date che richiedono il parsing a runtime (`pd.to_datetime`)
- Categoriche che vanno da 1 valore unico (`source`) a 434 (`organization`)
- Tre colonne completamente vuote (100% NaN)
- Una colonna identificatore (`link`)

Il dataset esercita ogni ramo dell'algoritmo di rilevamento.

---

## Stack tecnico

| Tool | Ruolo |
|---|---|
| Python 3.10+ | Linguaggio principale |
| pandas | Caricamento dati, analisi, formattazione della visualizzazione |
| argparse | Interfaccia CLI |
| uv | Gestione dei pacchetti |

Type hints completi e docstring in stile Google in tutto il codice.

---

## Contesto del progetto

Prism fa parte di un portfolio costruito durante una transizione di carriera verso AI e sviluppo software, insieme a:

- [Pulsar](https://github.com/boccassinisergio-afk/PULSAR) - tracker di output con motore regex data-driven e architettura OOP
- [Synapse](https://github.com/boccassinisergio-afk/Synapse) - tracker di concetti, abbinato a Pulsar come suite emit/absorb

---

## Autore

**Sergio Boccassini**
[GitHub](https://github.com/boccassinisergio-afk) - [LinkedIn](https://linkedin.com/in/sergio-boccassini) - [X](https://x.com/boccassini_ai)

<br><br>

---
---

<a name="english"></a>

# Prism
### Pandas Report & Intelligent Summary Maker

**[🇮🇹 Italiano](#prism) | 🇬🇧 English**

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