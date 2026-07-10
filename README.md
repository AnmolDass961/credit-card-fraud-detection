# 🛡️ Fraud Sentinel — Real-Time Fraud Detection

An XAI-powered fraud detection system for mobile-money transactions. An XGBoost model, trained on a downsampled slice of the PaySim dataset, is served through a FastAPI backend and explored through a Streamlit dashboard that explains every prediction with SHAP values.

### 🔗 Live

| | |
|---|---|
| **App** | [fraud-sentinel.streamlit.app](https://fraud-sentinel.streamlit.app/) |
| **API** | [credit-card-fraud-detection-oxvc.onrender.com](https://credit-card-fraud-detection-oxvc.onrender.com/health) |

> Both are on free tiers. The API spins down after 15 min idle — if the app's first prediction hangs for ~30–60s, that's it waking up, not a bug.

---

## 📑 Table of Contents

- [Project Structure](#-project-structure)
- [Dataset](#-dataset)
- [Pipeline](#-pipeline)
- [Model Performance](#-model-performance)
- [Tech Stack](#️-tech-stack)
- [Getting Started](#-getting-started-local)
- [API Reference](#-api-reference)
- [Deployment](#️-deployment)
- [License](#-license)

---

## 📁 Project Structure

```
.
├── api.py                          # FastAPI backend — serves predictions + SHAP explanations
├── app.py                          # Streamlit frontend — "Fraud Sentinel" dashboard
├── fraud_detection.ipynb           # EDA, model training & evaluation notebook
├── fraud_detection_model.pkl       # Trained XGBoost pipeline + tuned threshold (loaded by api.py)
├── requirements.txt                # Python dependencies
└── README.md
```

---

## 📦 Dataset

- **Source:** [PaySim](https://www.kaggle.com/datasets/ntnu-testimon/paysim1) — synthetic mobile-money transaction simulator, 6.36M rows
- **Sampling:** the full dataset is heavily imbalanced (~0.13% fraud), so it's downsampled to **1,000,000 rows** — all 8,213 fraud cases kept, plus a random sample of legitimate transactions — giving a working fraud rate of **~0.82%**
- **Fraud transaction types:** only occurs in `CASH_OUT` and `TRANSFER`

The raw CSV is **not** included in this repo (see `.gitignore`) — it's only needed for retraining, not for serving predictions.

---

## 🔬 Pipeline

```
Raw CSV
  │
  ├── Sampling       → downsample legit class to ~1M rows for tractable training
  ├── EDA            → class imbalance, fraud-by-type, amount/time patterns, correlations
  ├── Modelling      → XGBoost, no engineered features — raw fields only
  ├── Threshold tune → sweep validation set, pick threshold that maximises F1
  ├── Hyperparameters→ RandomizedSearchCV (n_estimators, max_depth, learning_rate, subsample, colsample_bytree)
  ├── Evaluation     → ROC-AUC, F1/F2, confusion matrix on held-out test set
  ├── Explainability → SHAP (TreeExplainer) — global + per-prediction
  └── Deployment     → FastAPI on Render + Streamlit on Community Cloud
```

**Features used:** `step`, `type`, `amount`, `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest` — raw transaction fields only, no engineered columns.

Full methodology is documented in `fraud_detection.ipynb`.

---

## 📊 Model Performance

Final tuned model, evaluated on a held-out test set (30% of the sampled data, untouched during training/tuning):

| Metric | Score |
|---|---|
| ROC-AUC | 0.9992 |
| Recall (Fraud) | ~96% |
| Precision (Fraud) | ~89% |
| F2 Score | ~94% |

---

## 🛠️ Tech Stack

- **Model:** XGBoost, scikit-learn (`ColumnTransformer` + `Pipeline`)
- **Explainability:** SHAP (`TreeExplainer`)
- **Backend:** FastAPI, Uvicorn, Pydantic — hosted on **Render**
- **Frontend:** Streamlit, Plotly — hosted on **Streamlit Community Cloud**

---

## 🔌 API Reference

Base URL: `https://credit-card-fraud-detection-oxvc.onrender.com`

### `GET /health`
```json
{ "status": "ok" }
```

### `POST /predict`

**Request body**

| Field | Type | Notes |
|---|---|---|
| `step` | int | Hour step of the simulation (≥ 0) |
| `type` | string | One of `CASH_OUT`, `TRANSFER`, `DEBIT`, `PAYMENT`, `CASH_IN` |
| `amount` | float | Transaction amount (≥ 0) |
| `oldbalanceOrg` | float | Origin balance before transaction |
| `newbalanceOrig` | float | Origin balance after transaction |
| `oldbalanceDest` | float | Destination balance before transaction |
| `newbalanceDest` | float | Destination balance after transaction |

```json
{
  "step": 1,
  "type": "CASH_OUT",
  "amount": 150000.00,
  "oldbalanceOrg": 150000.00,
  "newbalanceOrig": 0.00,
  "oldbalanceDest": 0.00,
  "newbalanceDest":  150000.00
}
```

**Response**

```json
{
  "prediction": 1,
  "probability": 0.87,
  "risk_level": "HIGH",
  "threshold_used": 0.3,
  "explanations": {
    "num__amount": 0.42,
    "cat__type_TRANSFER": 0.31,
    "num__oldbalanceOrg": 0.18
  }
}
```

- `prediction` — `1` = fraud, `0` = legitimate, based on `probability >= threshold_used`
- `risk_level` — `HIGH` (≥ 0.7), `MEDIUM` (≥ 0.3), or `LOW`
- `explanations` — per-feature SHAP values (positive → pushes toward fraud, negative → pushes toward legit)

---

## ☁️ Deployment

Backend and frontend are deployed **independently**, on two different platforms:

### Backend — Render
- Web Service, connected to this repo
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Live at: `https://credit-card-fraud-detection-oxvc.onrender.com`

### Frontend — Streamlit Community Cloud
- [share.streamlit.io](https://share.streamlit.io) → "Create app" → point at this repo, branch `main`, file `app.py`
  (root-level secrets are also exposed as environment variables, so `os.environ.get("API_URL", ...)` in `app.py` picks this up automatically)
- Live at: `https://fraud-sentinel.streamlit.app`

**.gitignore**
```
.venv/
__pycache__/
*.pyc
*.csv
```
