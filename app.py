import streamlit as st
import pandas as pd
import requests
import math
import plotly.graph_objects as go

st.set_page_config(
    page_title="Fraud Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #0d0f14; color: #e2e8f0; }

[data-testid="stSidebar"] {
    background-color: #111318 !important;
    border-right: 1px solid #1e2330;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* Header */
.sentinel-header {
    display: flex; align-items: center; gap: 14px;
    padding: 28px 0 8px 0;
    border-bottom: 1px solid #1e2330;
    margin-bottom: 28px;
}
.sentinel-header h1 {
    font-size: 1.55rem; font-weight: 700;
    color: #f1f5f9; margin: 0; letter-spacing: -0.3px;
}
.sentinel-header .sub {
    font-size: 0.78rem; color: #64748b; margin-top: 2px;
    font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px;
}

/* Metric cards */
.metric-row { display: flex; gap: 14px; margin-bottom: 24px; }
.metric-card {
    flex: 1; background: #151820;
    border: 1px solid #1e2330; border-radius: 10px; padding: 18px 20px;
}
.metric-card .label {
    font-size: 0.7rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 1px;
    font-weight: 600; margin-bottom: 6px;
}
.metric-card .value {
    font-size: 1.65rem; font-weight: 700;
    font-family: 'JetBrains Mono', monospace; line-height: 1;
}
.metric-card .value.green  { color: #22c55e; }
.metric-card .value.yellow { color: #f59e0b; }
.metric-card .value.red    { color: #ef4444; }
.metric-card .hint { font-size: 0.72rem; color: #475569; margin-top: 5px; }

/* Verdict banner */
.verdict {
    border-radius: 10px; padding: 20px 24px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px;
}
.verdict.low    { background: #052e16; border: 1px solid #166534; }
.verdict.medium { background: #1c1203; border: 1px solid #854d0e; }
.verdict.high   { background: #1f0808; border: 1px solid #991b1b; }
.verdict .icon  { font-size: 2rem; line-height: 1; }
.verdict .vtitle { font-size: 1.1rem; font-weight: 700; margin-bottom: 3px; }
.verdict .vtitle.low    { color: #4ade80; }
.verdict .vtitle.medium { color: #fbbf24; }
.verdict .vtitle.high   { color: #f87171; }
.verdict .action { font-size: 0.82rem; color: #94a3b8; }

/* Prob bar */
.prob-bar-wrap {
    background: #151820; border: 1px solid #1e2330;
    border-radius: 10px; padding: 18px 20px; margin-bottom: 24px;
}
.prob-bar-label {
    font-size: 0.7rem; color: #64748b; text-transform: uppercase;
    letter-spacing: 1px; font-weight: 600; margin-bottom: 10px;
}
.prob-track {
    background: #1e2330; border-radius: 999px;
    height: 10px; margin-bottom: 8px; overflow: hidden;
}
.prob-fill { height: 10px; border-radius: 999px; }
.prob-ticks {
    display: flex; justify-content: space-between;
    font-size: 0.68rem; color: #475569;
    font-family: 'JetBrains Mono', monospace; margin-top: 4px;
}

/* Idle */
.idle-box {
    background: #151820; border: 1px dashed #1e2330;
    border-radius: 12px; padding: 56px 24px; text-align: center;
}
.idle-box .idle-icon { font-size: 2.8rem; margin-bottom: 12px; }
.idle-box .idle-title { font-size: 1rem; font-weight: 600; color: #e2e8f0; margin-bottom: 6px; }
.idle-box .idle-sub   { font-size: 0.8rem; color: #475569; }

/* Section header */
.section-label {
    font-size: 0.68rem; color: #64748b; text-transform: uppercase;
    letter-spacing: 1.2px; font-weight: 700; margin-bottom: 10px;
}

.block-container { padding-top: 1rem !important; }

/* Native metric card dark override */
[data-testid="stMetric"] {
    background: #151820 !important;
    border: 1px solid #1e2330 !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
}
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.72rem !important; }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-family: 'JetBrains Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sentinel-header">
  <div style="font-size:2rem">🛡️</div>
  <div>
    <h1>Fraud Sentinel</h1>
    <div class="sub">XAI-POWERED · XGBOOST · REAL-TIME ANALYSIS</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Transaction Input")
    st.markdown("**Transaction**")
    step     = st.number_input("Time Step (hours)", min_value=0, value=1)
    type_val = st.selectbox("Type", ['CASH_OUT', 'TRANSFER', 'DEBIT', 'PAYMENT', 'CASH_IN'])
    amount   = st.number_input("Amount ($)", min_value=0.0, value=150000.0, format="%.2f")

    st.markdown("**Origin Account**")
    oldbalanceOrg  = st.number_input("Balance Before", min_value=0.0, value=150000.0, format="%.2f")
    newbalanceOrig = st.number_input("Balance After",  min_value=0.0, value=0.0,      format="%.2f")

    st.markdown("**Destination Account**")
    oldbalanceDest = st.number_input("Balance Before ", min_value=0.0, value=0.0, format="%.2f")
    newbalanceDest = st.number_input("Balance After ",  min_value=0.0, value=0.0, format="%.2f")

    st.markdown("---")
    analyze = st.button("🔍 Analyze Transaction", type="primary", use_container_width=True)

# ── Idle state ────────────────────────────────────────────────────────────────
if not analyze:
    st.markdown("""
    <div class="idle-box">
      <div class="idle-icon">🔬</div>
      <div class="idle-title">Ready to Analyze</div>
      <div class="idle-sub">Fill in transaction details on the left and click Analyze.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── API call ──────────────────────────────────────────────────────────────────
with st.spinner("Running model inference..."):
    payload = {
        "step": step, "type": type_val, "amount": amount,
        "oldbalanceOrg": oldbalanceOrg, "newbalanceOrig": newbalanceOrig,
        "oldbalanceDest": oldbalanceDest, "newbalanceDest": newbalanceDest
    }
    try:
        response = requests.post("https://credit-card-fraud-detection-oxvc.onrender.com", json=payload, timeout=10)
        result = response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Run: `uvicorn main:app --reload`")
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API error: {e}")
        st.stop()

proba     = result['probability']
risk      = result['risk_level']
threshold = result.get('threshold_used', 0.15)
risk_cls  = risk.lower()
pct       = proba * 100

# ── Verdict banner ────────────────────────────────────────────────────────────
actions = {
    "HIGH":   "🚨 Block transaction immediately. Freeze origin account pending manual review.",
    "MEDIUM": "⚠️ Flag for secondary analyst review. Do not process until cleared.",
    "LOW":    "✅ Allow transaction to proceed normally.",
}
icons = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}

st.markdown(f"""
<div class="verdict {risk_cls}">
  <div class="icon">{icons[risk]}</div>
  <div>
    <div class="vtitle {risk_cls}">{risk} RISK</div>
    <div class="action">{actions[risk]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Metric cards (native st.metric for reliability) ───────────────────────────
val_color = "green" if risk == "LOW" else ("yellow" if risk == "MEDIUM" else "red")
pred_txt  = "FRAUD 🔴" if result['prediction'] == 1 else "LEGIT 🟢"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Fraud Probability", f"{pct:.1f}%", help=f"Threshold: {threshold}")
with col2:
    st.metric("Prediction", pred_txt)
with col3:
    st.metric("Risk Level", risk)
with col4:
    st.metric("Amount", f"${amount:,.0f}", help=type_val)

st.markdown("<br>", unsafe_allow_html=True)

# ── Probability bar ───────────────────────────────────────────────────────────
bar_color = "#22c55e" if risk == "LOW" else ("#f59e0b" if risk == "MEDIUM" else "#ef4444")
bar_w     = min(int(pct), 100)

st.markdown(f"""
<div class="prob-bar-wrap">
  <div class="prob-bar-label">Fraud Score Distribution</div>
  <div class="prob-track">
    <div class="prob-fill" style="width:{bar_w}%;background:{bar_color};"></div>
  </div>
  <div class="prob-ticks">
    <span>0% — Safe</span>
    <span>30% — Medium</span>
    <span>70% — High</span>
    <span>100% — Certain Fraud</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Signal checks (native Streamlit — no HTML) ───────────────────────────────
st.markdown("---")
st.markdown("**🔍 Rule-Based Signals**")

origin_drained  = newbalanceOrig == 0 and oldbalanceOrg > 0
dest_was_empty  = oldbalanceDest == 0
amount_full_bal = math.isclose(amount, oldbalanceOrg, rel_tol=0.01)
bal_err         = abs((oldbalanceOrg - newbalanceOrig) - amount)
off_hour        = (step % 24 < 9) or (step % 24 > 21)
depletion_pct   = (amount / (oldbalanceOrg + 1)) * 100

s1, s2, s3, s4, s5, s6 = st.columns(6)
with s1: st.metric("Origin Drained",    "🚩 YES" if origin_drained  else "✅ NO",  f"${newbalanceOrig:,.0f} left")
with s2: st.metric("Dest Was Empty",    "🚩 YES" if dest_was_empty  else "✅ NO",  f"${oldbalanceDest:,.0f} prior")
with s3: st.metric("Amount = Balance",  "🚩 YES" if amount_full_bal else "✅ NO",  f"${amount:,.0f} sent")
with s4: st.metric("Balance Error",     "🚩 YES" if bal_err > 1     else "✅ NO",  f"${bal_err:,.0f} discrepancy")
with s5: st.metric("Off-Hours",         "🚩 YES" if off_hour        else "✅ NO",  f"Hour {step%24:02d}:00")
with s6: st.metric("Depletion Rate",    "🚩 YES" if depletion_pct>90 else "✅ NO", f"{depletion_pct:.1f}% of balance")

st.markdown("<br>", unsafe_allow_html=True)

# ── Plain-English SHAP explanation (native Streamlit — no HTML) ──────────────
FEAT_MAP = {
    "error_diff":     ("💸 Balance Mismatch",      "Money left the origin but didn't arrive as expected — accounting inconsistency that's near-impossible in legitimate transactions."),
    "orig_depletion": ("🔻 Account Drain Rate",    "Origin sent a very large fraction of its total balance. Fraudsters typically drain accounts in one go rather than partial amounts."),
    "orig_drained_0": ("🚨 Origin Wiped to Zero",  "Origin balance hit exactly zero after this transfer — a hallmark pattern in fraudulent account takeovers."),
    "dest_was_empty": ("👤 Destination Was Empty", "The recipient account had no funds before receiving money — classic indicator of a mule account set up just to receive stolen funds."),
    "is_off_hour":    ("🌙 Off-Hours Transfer",    "Transaction occurred outside normal banking hours (9am–9pm) when human review teams are understaffed and fraud goes unnoticed."),
    "hour":           ("🕐 Transaction Hour",      "The time of day influences fraud probability — late-night and early-morning transfers show higher fraud rates in the training data."),
    "amount":         ("💰 Transaction Amount",    "The transfer size is unusual relative to what the model has learned from 6M+ transactions in the PaySim dataset."),
    "type_CASH_OUT":  ("⚡ Cash-Out Type",         "CASH_OUT is one of only two transaction types where fraud occurs in this dataset — all other types have zero fraud cases."),
    "type_TRANSFER":  ("⚡ Transfer Type",         "TRANSFER is one of only two transaction types associated with fraud — raises the model's baseline probability significantly."),
    "oldbalanceOrg":  ("📊 Origin Start Balance",  "How much was in the origin account before the transaction — context for judging how suspicious the withdrawn amount is."),
    "newbalanceOrig": ("📊 Origin End Balance",    "What remained in origin after the transaction — unexpectedly low or zero values strongly signal drain-based fraud."),
    "oldbalanceDest": ("📊 Dest Prior Balance",    "How much was already in the destination account before receiving funds — zero balances indicate purpose-built mule accounts."),
    "newbalanceDest": ("📊 Dest Final Balance",    "Destination balance after receiving — if it didn't increase by the expected amount, money was likely passed through immediately."),
}

def get_explanation(raw, impact):
    clean     = raw.replace("num__", "").replace("cat__", "")
    direction = "toward **FRAUD** ↑" if impact > 0 else "toward **LEGIT** ↓"
    strength  = "strongly" if abs(impact) > 0.3 else ("moderately" if abs(impact) > 0.1 else "slightly")
    for key, (label, desc) in FEAT_MAP.items():
        if key in clean:
            return label, f"{desc} → pushed score **{strength}** {direction}"
    return clean, f"Pushed score **{strength}** {direction}"

explanations = result.get('explanations', {})
if explanations:
    top = sorted(explanations.items(), key=lambda x: abs(x[1]), reverse=True)
    top = [(f, v) for f, v in top if abs(v) > 0.01][:6]

    if top:
        st.markdown("---")
        st.markdown("**🤖 Why did the model decide this?**")
        st.caption("Top features driving this prediction, explained in plain English.")

        for feat, impact in top:
            label, text = get_explanation(feat, impact)
            color  = "#ef4444" if impact > 0 else "#22c55e"
            symbol = "🔴" if impact > 0 else "🟢"
            with st.container():
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.markdown(
                        f'<div style="background:#1a1a2e;border-left:3px solid {color};'
                        f'border-radius:4px;padding:8px 12px;font-family:JetBrains Mono,monospace;'
                        f'font-size:0.78rem;color:#e2e8f0">{symbol} {label}</div>',
                        unsafe_allow_html=True
                    )
                with col_b:
                    st.markdown(
                        f'<div style="background:#0f1318;border-radius:4px;padding:8px 12px;'
                        f'font-size:0.8rem;color:#c9d1d9;line-height:1.6">{text}</div>',
                        unsafe_allow_html=True
                    )
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

    # ── SHAP chart ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">📊 Feature Impact (SHAP Values)</div>', unsafe_allow_html=True)

    import plotly.graph_objects as go
    shap_df = (
        pd.DataFrame(list(explanations.items()), columns=['Feature', 'Impact'])
        .assign(Abs=lambda d: d['Impact'].abs())
        .sort_values('Abs', ascending=True).tail(8)
        .reset_index(drop=True)
    )
    shap_df['Feature'] = (
        shap_df['Feature']
        .str.replace('num__', '', regex=False)
        .str.replace('cat__', '', regex=False)
    )
    shap_df['Color'] = shap_df['Impact'].apply(lambda x: '#ef4444' if x > 0 else '#22c55e')
    shap_df['Label'] = shap_df['Impact'].apply(lambda x: f"+{x:.4f}" if x > 0 else f"{x:.4f}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=shap_df['Impact'], y=shap_df['Feature'], orientation='h',
        marker_color=shap_df['Color'],
        text=shap_df['Label'], textposition='outside',
        textfont=dict(color='#94a3b8', size=11, family='JetBrains Mono'),
        hovertemplate='<b>%{y}</b><br>SHAP: %{x:.4f}<extra></extra>',
    ))
    fig.update_layout(
        paper_bgcolor='#151820', plot_bgcolor='#151820',
        font=dict(family='Inter', color='#94a3b8', size=12),
        xaxis=dict(
            gridcolor='#1e2330', zerolinecolor='#2d3748',
            title=dict(text='← Pushes to Legit   |   Pushes to Fraud →', font=dict(color='#64748b', size=11)),
            tickfont=dict(family='JetBrains Mono', color='#64748b'),
        ),
        yaxis=dict(gridcolor='#1e2330', tickfont=dict(family='JetBrains Mono', color='#94a3b8', size=11)),
        margin=dict(l=20, r=70, t=10, b=40),
        height=300, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        '<div style="font-size:0.7rem;color:#64748b;margin-top:-10px">'
        '🔴 Positive SHAP = pushes toward <b style="color:#ef4444">FRAUD</b> &nbsp;|&nbsp; '
        '🟢 Negative SHAP = pushes toward <b style="color:#22c55e">LEGIT</b> &nbsp;|&nbsp; '
        'Bar length = strength of influence'
        '</div>',
        unsafe_allow_html=True
    )