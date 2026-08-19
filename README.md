# KPT Complaint Management System — Data Analysis & Dashboard

A complete end-to-end project that analyzes complaint data (category, sentiment,
timing patterns, resolution behavior) and presents it in an interactive dashboard.

Built with: **Python + MySQL + Streamlit**

---

## Real-World Deployment Notes

This project was deployed and tested in an offline, air-gapped environment 
(no internet access) as part of an internship engagement, involving:
- Offline installation of Python, MySQL, and all dependencies via manual package transfer
- Resolving enterprise security software (endpoint protection) conflicts with local development tools
- Adapting the setup for a Windows Server LAN environment

📄 See [DEPLOYMENT.md](DEPLOYMENT.md) for full technical documentation of this process.

## What This Project Does

1. **Stores** complaint data in a MySQL database
2. **Cleans** raw complaint text and metadata
3. **Classifies** each complaint by category (what kind of complaint)
4. **Scores sentiment** (positive/negative/neutral tone of the complaint)
5. **Analyzes timing** — which hours/days/months see the most complaints
6. **Predicts resolution time** using a regression model (bonus feature)
7. **Visualizes everything** in an interactive Streamlit dashboard

Since real KPT data wasn't provided, `data/generate_sample_data.py` creates a
realistic **synthetic dataset** (2,500 complaints) so the whole pipeline runs
immediately. **Replace it with your real KPT export** and the rest of the
pipeline works unchanged — just make sure your CSV has the same column names
(see "Using Your Own Data" below).

---

## Folder Structure

```
kpt_complaint_analysis/
├── README.md                      <- you are here
├── requirements.txt                <- all Python dependencies
├── config.py                       <- MySQL connection settings (edit this)
│
├── database/
│   └── schema.sql                  <- MySQL table definitions
│
├── data/
│   └── generate_sample_data.py     <- creates synthetic complaint dataset
│
├── src/
│   ├── 01_load_to_mysql.py         <- loads CSV data into MySQL
│   ├── 02_data_cleaning.py         <- cleans text & handles missing data
│   ├── 03_sentiment_analysis.py    <- VADER + Transformer sentiment scoring
│   ├── 04_categorization.py        <- TF-IDF + ML complaint category classifier
│   ├── 05_time_analysis.py         <- peak hour/day/month analysis + charts
│   ├── 06_resolution_prediction.py <- predicts resolution time (regression)
│   └── 07_save_results_to_mysql.py <- writes all results back to MySQL
│
├── dashboard/
│   └── app.py                      <- Streamlit dashboard (main deliverable)
│
└── outputs/                        <- charts, model files, and processed CSVs land here
```

---

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up MySQL
- Create a database:
```sql
CREATE DATABASE kpt_complaints;
```
- Run the schema file:
```bash
mysql -u root -p kpt_complaints < database/schema.sql
```
- Edit `config.py` with your MySQL username, password, host, and database name.

### 3. Generate (or replace with real) data
```bash
python data/generate_sample_data.py
```
This creates `data/complaints_raw.csv`. **To use real KPT data, just place your
own CSV at this path with matching column names** (see below).

### 4. Run the pipeline in order
```bash
python src/01_load_to_mysql.py
python src/02_data_cleaning.py
python src/03_sentiment_analysis.py
python src/04_categorization.py
python src/05_time_analysis.py
python src/06_resolution_prediction.py
python src/07_save_results_to_mysql.py
```

Each script reads from / writes to MySQL and drops supporting files into `outputs/`.

### 5. Launch the dashboard
```bash
streamlit run dashboard/app.py
```
Opens in your browser at `http://localhost:8501`.

---

## Using Your Own KPT Data

Your CSV (or MySQL export) should ideally have these columns — rename your real
columns to match, or edit `config.py` → `COLUMN_MAP` to map your actual column
names instead:

| Column            | Description                                   |
|-------------------|------------------------------------------------|
| complaint_id      | Unique ID                                       |
| complaint_text    | The written complaint (used for NLP)            |
| category          | (optional — leave blank if unlabeled, the categorization script will predict it) |
| date_received     | Timestamp complaint was filed                   |
| date_resolved     | Timestamp complaint was closed (blank if open)  |
| status            | Open / In Progress / Resolved / Closed          |
| department        | Department responsible                          |
| customer_id       | Customer identifier (can be anonymized)         |

If your data is in Urdu / Roman Urdu, see the note inside
`src/02_data_cleaning.py` — there's a toggle for basic Urdu stopword handling.

---

## Models Used (and why)

| Task                     | Model                                              | Why                                             |
|---------------------------|-----------------------------------------------------|--------------------------------------------------|
| Sentiment (baseline)      | VADER (rule-based)                                  | Fast, no training needed, decent baseline         |
| Sentiment (accurate)      | HuggingFace DistilBERT (`sst-2`)                    | Much better accuracy on nuanced complaint text    |
| Category classification   | TF-IDF + Logistic Regression (+ Naive Bayes compare)| Interpretable, fast, works well on moderate data  |
| Time pattern analysis     | Pandas groupby + Seaborn/Plotly                     | No model needed — pure statistical aggregation    |
| Resolution time prediction| Random Forest Regressor                             | Handles mixed feature types, robust to outliers   |

The scripts print accuracy/comparison metrics so you can discuss model choice
and performance in your report.

---

## What You Can Add Beyond This (Extension Ideas)

These are already scaffolded with TODO comments in the code, or easy to bolt on:

- **Auto-routing**: predict which department a new complaint should go to
- **Urgency/priority scoring**: classify complaints as high/medium/low priority
- **Forecasting**: use Prophet/ARIMA on `05_time_analysis.py` output to predict next month's complaint volume
- **Word clouds** per category (helper included in `05_time_analysis.py`)
- **Anomaly detection**: flag unusual spikes in daily complaint counts
- **Customer satisfaction score**: combine sentiment + resolution speed into one KPI
- **Auto-reply drafting**: use an LLM to draft a first-response suggestion per complaint

---

## Notes for Your Report/Presentation

- The synthetic dataset mimics realistic complaint patterns (more complaints in
  summer months for a utility company, more billing complaints than others,
  etc.) so your peak-time and category charts will look meaningful even before
  you plug in real data.
- Swap in real KPT data as early as possible — synthetic patterns are for
  testing the pipeline, not for your actual conclusions.
- All model files (`.pkl`) are saved in `outputs/models/` so you don't need to
  retrain every time you open the dashboard.
