"""
KPT Complaint Management System — Interactive Dashboard

"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

from config import get_sqlalchemy_uri, FINAL_CSV

st.set_page_config(page_title="KPT Complaint Dashboard", layout="wide", page_icon="📋")


@st.cache_data(ttl=300)
def load_data():
    try:
        engine = create_engine(get_sqlalchemy_uri())
        df = pd.read_sql("SELECT * FROM complaints_full_view", engine)
        df["date_received"] = pd.to_datetime(df["date_received"])
        source = "MySQL (live)"
        return df, source
    except Exception:
        df = pd.read_csv(FINAL_CSV)
        df["date_received"] = pd.to_datetime(df["date_received"])
        if "final_category" not in df.columns:
            df["final_category"] = df.get("category", df.get("predicted_category"))
        source = "Local CSV (MySQL not reachable)"
        return df, source


df, source = load_data()

st.title("📋 KPT Complaint Management — Analysis Dashboard")
st.caption(f"Data source: {source} · {len(df)} complaints loaded")

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

cat_col = "final_category" if "final_category" in df.columns else "category"
categories = sorted(df[cat_col].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

sentiments = sorted(df["sentiment_label"].dropna().unique().tolist())
selected_sentiments = st.sidebar.multiselect("Sentiment", sentiments, default=sentiments)

min_date, max_date = df["date_received"].min(), df["date_received"].max()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date))

if "department" in df.columns:
    departments = sorted(df["department"].dropna().unique().tolist())
    selected_departments = st.sidebar.multiselect("Department", departments, default=departments)
else:
    selected_departments = None

# Apply filters
filtered = df[
    df[cat_col].isin(selected_categories) &
    df["sentiment_label"].isin(selected_sentiments)
]
if len(date_range) == 2:
    filtered = filtered[
        (filtered["date_received"] >= pd.Timestamp(date_range[0])) &
        (filtered["date_received"] <= pd.Timestamp(date_range[1]) + pd.Timedelta(days=1))
    ]
if selected_departments is not None:
    filtered = filtered[filtered["department"].isin(selected_departments)]

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Complaints", f"{len(filtered):,}")

neg_pct = (filtered["sentiment_label"] == "Negative").mean() * 100 if len(filtered) else 0
col2.metric("Negative Sentiment %", f"{neg_pct:.1f}%")

if "resolution_time_hours" in filtered.columns:
    avg_res = filtered["resolution_time_hours"].dropna().mean()
    col3.metric("Avg Resolution Time", f"{avg_res:.0f} hrs" if pd.notna(avg_res) else "N/A")
else:
    col3.metric("Avg Resolution Time", "N/A")

if "status" in filtered.columns:
    open_pct = (filtered["status"].isin(["Open", "In Progress"])).mean() * 100
    col4.metric("Currently Open %", f"{open_pct:.1f}%")
else:
    col4.metric("Currently Open %", "N/A")

st.divider()

# ---------------------------------------------------------------------------
# Row 1: Category breakdown + Sentiment breakdown
# ---------------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Complaints by Category")
    cat_counts = filtered[cat_col].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig = px.bar(cat_counts, x="Count", y="Category", orientation="h", color="Category")
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Sentiment Distribution")
    sent_counts = filtered["sentiment_label"].value_counts().reset_index()
    sent_counts.columns = ["Sentiment", "Count"]
    color_map = {"Positive": "#55A868", "Negative": "#C44E52", "Neutral": "#8172B2"}
    fig = px.pie(sent_counts, names="Sentiment", values="Count",
                 color="Sentiment", color_discrete_map=color_map, hole=0.4)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 2: Time patterns
# ---------------------------------------------------------------------------
st.subheader("When Do Complaints Happen Most?")
t1, t2, t3 = st.columns(3)

with t1:
    if "complaint_hour" in filtered.columns:
        hourly = filtered["complaint_hour"].value_counts().sort_index().reset_index()
        hourly.columns = ["Hour", "Count"]
        fig = px.line(hourly, x="Hour", y="Count", markers=True, title="By Hour of Day")
        st.plotly_chart(fig, use_container_width=True)

with t2:
    if "complaint_day_of_week" in filtered.columns:
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily = filtered["complaint_day_of_week"].value_counts().reindex(order).reset_index()
        daily.columns = ["Day", "Count"]
        fig = px.bar(daily, x="Day", y="Count", title="By Day of Week")
        st.plotly_chart(fig, use_container_width=True)

with t3:
    if "complaint_month" in filtered.columns:
        order = ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        monthly = filtered["complaint_month"].value_counts().reindex(order).reset_index()
        monthly.columns = ["Month", "Count"]
        fig = px.bar(monthly, x="Month", y="Count", title="By Month")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 3: Category vs Month heatmap
# ---------------------------------------------------------------------------
st.subheader("Category Trends Across Months")
order = ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"]
pivot = pd.crosstab(filtered[cat_col], filtered["complaint_month"])
pivot = pivot.reindex(columns=[m for m in order if m in pivot.columns])
fig = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="YlOrRd",
                 labels=dict(x="Month", y="Category", color="Complaints"))
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 4: Sentiment over time + Department load
# ---------------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Sentiment Trend Over Time")
    monthly_sent = filtered.groupby([filtered["date_received"].dt.to_period("M").astype(str), "sentiment_label"]).size().reset_index(name="Count")
    monthly_sent.columns = ["Month", "Sentiment", "Count"]
    fig = px.bar(monthly_sent, x="Month", y="Count", color="Sentiment",
                 color_discrete_map=color_map, barmode="stack")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    if "department" in filtered.columns:
        st.subheader("Complaint Load by Department")
        dept_counts = filtered["department"].value_counts().reset_index()
        dept_counts.columns = ["Department", "Count"]
        fig = px.bar(dept_counts, x="Department", y="Count", color="Department")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 5: Resolution time analysis
# ---------------------------------------------------------------------------
if "resolution_time_hours" in filtered.columns and filtered["resolution_time_hours"].notna().any():
    st.subheader("Resolution Time by Category")
    fig = px.box(filtered.dropna(subset=["resolution_time_hours"]),
                 x=cat_col, y="resolution_time_hours", color=cat_col)
    fig.update_layout(showlegend=False, yaxis_title="Resolution Time (hours)")
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Raw data explorer
# ---------------------------------------------------------------------------
st.divider()
with st.expander("🔍 Browse Raw Complaint Data"):
    display_cols = [c for c in [
        "complaint_id", "complaint_text", cat_col, "department", "status",
        "sentiment_label", "date_received", "resolution_time_hours"
    ] if c in filtered.columns]
    st.dataframe(filtered[display_cols].sort_values("date_received", ascending=False), use_container_width=True)

# ---------------------------------------------------------------------------
# NEW SECTION: Classify a New Complaint (category unknown / possibly wrong)
# ---------------------------------------------------------------------------
st.divider()
st.header("🆕 Classify a New Complaint (Category Unknown)")
st.caption("Predicts category and sentiment directly from complaint text — no category needed. Useful for catching miscategorized complaints before they skew the statistics above.")

new_complaint = st.text_area(
    "Paste a complaint below (category not needed):",
    height=100,
    placeholder="e.g. I have been waiting three weeks and no one has responded to my request."
)

if st.button("Classify Complaint"):
    if new_complaint.strip() == "":
        st.warning("Please enter some complaint text first.")
    else:
        try:
            import joblib, re, os as _os
            from config import MODEL_DIR
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

            model = joblib.load(_os.path.join(MODEL_DIR, "category_classifier.pkl"))
            vectorizer = joblib.load(_os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))

            # clean the text the same way the training data was cleaned
            clean = new_complaint.lower()
            clean = re.sub(r"http\S+|www\S+", "", clean)
            clean = re.sub(r"[^a-zA-Z\s]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()

            X = vectorizer.transform([clean])
            predicted_category = model.predict(X)[0]
            confidence = model.predict_proba(X).max() if hasattr(model, "predict_proba") else None

            analyzer = SentimentIntensityAnalyzer()
            compound = analyzer.polarity_scores(new_complaint)["compound"]
            sentiment = "Positive" if compound >= 0.05 else ("Negative" if compound <= -0.05 else "Neutral")

            r1, r2, r3 = st.columns(3)
            r1.metric("Predicted Category", predicted_category)
            r2.metric("Model Confidence", f"{confidence:.1%}" if confidence else "N/A")
            r3.metric("Predicted Sentiment", sentiment)

            st.info(
                f"The model predicts this complaint belongs to **{predicted_category}** "
                f"with **{sentiment.lower()}** sentiment — based purely on its wording, "
                f"with no category ever supplied."
            )

            if confidence and confidence < 0.5:
                st.warning(
                    "⚠️ Low confidence — this complaint's wording is ambiguous between "
                    "categories. Consider having a human double-check this one."
                )

        except FileNotFoundError:
            st.error("Model files not found. Run `python src/04_categorization.py` first to train the model.")

# ---------------------------------------------------------------------------
# NEW SECTION: Complaint Workflow — Routing & Resolution Journey
# ---------------------------------------------------------------------------
st.divider()
st.header("🔄 Complaint Workflow: From Filing to Resolution")
st.caption(
    "Tracks each complaint's journey: Public Relations receives it, forwards it to a "
    "department (correctly or by mistake), and it gets reviewed and resolved. "
    "This section shows how often complaints get sent to the wrong department first, "
    "and how much extra time that adds."
)

@st.cache_data(ttl=300)
def load_workflow_data():
    try:
        engine = create_engine(get_sqlalchemy_uri())
        wf = pd.read_sql("SELECT * FROM complaint_workflow", engine)
        wf["stage_timestamp"] = pd.to_datetime(wf["stage_timestamp"])
        return wf, "MySQL (live)"
    except Exception:
        wf = pd.read_csv(os.path.join(os.path.dirname(FINAL_CSV), "complaint_workflow.csv"))
        wf["stage_timestamp"] = pd.to_datetime(wf["stage_timestamp"])
        return wf, "Local CSV (MySQL not reachable)"

wf_df, wf_source = load_workflow_data()
st.caption(f"Workflow data source: {wf_source} · {wf_df['complaint_id'].nunique()} complaints tracked")

# --- KPIs ---
first_try = wf_df[wf_df["stage_order"] == 2]
misroute_rate = (first_try["routed_correctly"] == False).mean() * 100

process_time = wf_df.groupby("complaint_id")["stage_timestamp"].agg(["min", "max"])
process_time["total_hours"] = (process_time["max"] - process_time["min"]).dt.total_seconds() / 3600
routed_map = first_try.set_index("complaint_id")["routed_correctly"]
process_time["routed_correctly"] = process_time.index.map(routed_map)
avg_correct = process_time[process_time["routed_correctly"] == True]["total_hours"].mean()
avg_misrouted = process_time[process_time["routed_correctly"] == False]["total_hours"].mean()

wk1, wk2, wk3 = st.columns(3)
wk1.metric("First-Attempt Misrouting Rate", f"{misroute_rate:.1f}%")
wk2.metric("Avg. Process Time (Routed Correctly)", f"{avg_correct:.0f} hrs")
wk3.metric("Avg. Process Time (Misrouted)", f"{avg_misrouted:.0f} hrs", delta=f"+{avg_misrouted - avg_correct:.0f} hrs slower", delta_color="inverse")

# --- Misrouting rate by category ---
wcol1, wcol2 = st.columns(2)

with wcol1:
    st.subheader("Misrouting Rate by Category")
    cat_lookup = filtered[["complaint_id", cat_col]].drop_duplicates() if "complaint_id" in filtered.columns else df[["complaint_id", cat_col]].drop_duplicates()
    ft_with_cat = first_try.merge(cat_lookup, on="complaint_id", how="left")
    rate_by_cat = ft_with_cat.groupby(cat_col)["routed_correctly"].apply(lambda x: (x == False).mean() * 100).reset_index()
    rate_by_cat.columns = ["Category", "Misroute Rate (%)"]
    rate_by_cat = rate_by_cat.sort_values("Misroute Rate (%)", ascending=True)
    fig = px.bar(rate_by_cat, x="Misroute Rate (%)", y="Category", orientation="h", color="Category")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with wcol2:
    st.subheader("Where Misrouted Complaints Get Sent")
    misrouted_depts = first_try[first_try["routed_correctly"] == False]["department"].value_counts().reset_index()
    misrouted_depts.columns = ["Department (Wrongly Received)", "Count"]
    fig = px.bar(misrouted_depts, x="Count", y="Department (Wrongly Received)", orientation="h", color="Department (Wrongly Received)")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Complaint journey viewer ---
st.subheader("🔍 Track a Specific Complaint's Journey")
available_ids = sorted(wf_df["complaint_id"].unique().tolist())
selected_complaint_id = st.selectbox("Select a Complaint ID:", available_ids)

journey = wf_df[wf_df["complaint_id"] == selected_complaint_id].sort_values("stage_order")

for _, stage in journey.iterrows():
    icon = "📥" if stage["action"] == "Received" else ("⚠️" if "Incorrect" in str(stage["action"]) else ("✅" if stage["resolution_status"] == "Resolved" else "🔁"))
    with st.container(border=True):
        c1, c2 = st.columns([1, 4])
        c1.markdown(f"### {icon}")
        c2.markdown(f"**Stage {int(stage['stage_order'])}: {stage['department']}** — *{stage['action']}*")
        c2.write(stage["comment"])
        if pd.notna(stage["resolution_status"]):
            status_color = "green" if stage["resolution_status"] == "Resolved" else "orange"
            c2.markdown(f":{status_color}[**Final status: {stage['resolution_status']}**]")

st.caption("Built with Python, MySQL, and Streamlit · KPT Complaint Analysis Project")
