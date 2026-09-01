import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime, date, time, timedelta
from textwrap import dedent
import base64
from pathlib import Path
import io
import re

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FitGraph",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# BACKGROUND IMAGE
# ============================================================

def set_background(image_path):
    path = Path(image_path)
    if not path.exists():
        return
    encoded = base64.b64encode(path.read_bytes()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(160deg, rgba(8,10,20,0.72), rgba(15,10,25,0.72)),
                url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

set_background("pages/images/appbgpic.jpg")


# ============================================================
# MONGODB CONNECTION (shared by both Log Entry + Dashboard)
# ============================================================

MONGO_URI = (
    "mongodb+srv://soumyadeepdas2511:"
    "dxRsCQDq7YQSc1vh"
    "@cluster0.zmm4k.mongodb.net/"
    "?retryWrites=true&w=majority&appName=Cluster0"
)


@st.cache_resource
def connect_to_mongodb():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client


try:
    client = connect_to_mongodb()
    db = client["gym_tracker"]
    daily_logs_collection = db["daily_logs"]
    mongo_connected = True
except Exception as error:
    mongo_connected = False
    mongo_error = str(error)


# ============================================================
# CSS — DARK PREMIUM THEME (merged from both pages)
# ============================================================

st.markdown(
    """
<style>
* { scrollbar-width: thin; }

.stApp {
    color: #f2f3f7;
}

header[data-testid="stHeader"] { background: transparent; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 5rem;
    max-width: 1500px;
}

/* ============================================================
   TYPOGRAPHY
   ============================================================ */

.main-header { margin-bottom: 25px; }

.main-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1.2px;
    background: linear-gradient(90deg, #ffffff, #a9c3ff 60%, #c9a9ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 40px rgba(124, 158, 255, 0.25);
}

.main-subtitle {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.55);
    margin-top: 6px;
}

.blue-line {
    height: 1px;
    background: linear-gradient(90deg, rgba(124,158,255,0.9), rgba(124,158,255,0));
    margin-top: 20px;
    border-radius: 1px;
}

.dash-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #9db8ff, #c9a9ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
    text-shadow: 0 0 40px rgba(167, 139, 250, 0.2);
}
.dash-sub { color: rgba(255,255,255,0.55); margin-top: -6px; margin-bottom: 18px; }

/* ============================================================
   STATUS PILLS
   ============================================================ */

.database-online {
    display: inline-block;
    background: rgba(64, 209, 125, 0.12);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(64, 209, 125, 0.35);
    color: #6ee7a8;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    box-shadow: 0 0 18px rgba(64, 209, 125, 0.15);
}

.database-offline {
    display: inline-block;
    background: rgba(255, 92, 92, 0.12);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 92, 92, 0.35);
    color: #ff8787;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    box-shadow: 0 0 18px rgba(255, 92, 92, 0.15);
}

/* ============================================================
   SECTION HEADERS
   ============================================================ */

.section-header { margin-top: 28px; margin-bottom: 14px; }

.section-title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-description {
    font-size: 13px;
    color: rgba(255,255,255,0.45);
    margin-top: 3px;
}

/* ============================================================
   GLASS PANELS (containers, expanders)
   ============================================================ */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.045);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 18px;
    box-shadow:
        0 8px 32px rgba(0, 0, 0, 0.35),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(124, 158, 255, 0.25);
}

div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 14px;
}

/* ============================================================
   INPUTS
   ============================================================ */

.stNumberInput input,
.stTextInput input,
.stTextArea textarea {
    background-color: rgba(0, 0, 0, 0.35) !important;
    backdrop-filter: blur(8px);
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 10px !important;
}

.stNumberInput input:focus,
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(124, 158, 255, 0.55) !important;
    box-shadow: 0 0 0 3px rgba(124, 158, 255, 0.15) !important;
}

div[data-baseweb="select"] > div {
    background-color: rgba(0, 0, 0, 0.35) !important;
    backdrop-filter: blur(8px);
    border-color: rgba(255, 255, 255, 0.14) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}

label { color: rgba(255,255,255,0.75) !important; }

/* Sliders */
div[data-testid="stSlider"] [role="slider"] {
    box-shadow: 0 0 0 6px rgba(124, 158, 255, 0.18);
}

/* ============================================================
   BUTTONS
   ============================================================ */

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, rgba(124,158,255,0.9), rgba(167,139,250,0.9));
    backdrop-filter: blur(10px);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 12px;
    padding: 12px;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 20px rgba(124, 158, 255, 0.25);
    transition: 0.2s ease;
}

.stButton > button:hover {
    color: #ffffff;
    border-color: rgba(255,255,255,0.32);
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(124, 102, 241, 0.4);
}

.stButton > button:active {
    transform: translateY(0px);
}

.stDownloadButton > button {
    width: 100%;
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(10px);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: 12px;
    font-weight: 600;
    transition: 0.2s ease;
}

.stDownloadButton > button:hover {
    border-color: rgba(124, 158, 255, 0.5);
    background: rgba(124, 158, 255, 0.10);
}

/* ============================================================
   CALCULATED / COUNTDOWN GLASS BOXES
   ============================================================ */

.calculated-box {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 14px;
    padding: 18px;
    margin-top: 10px;
}

.calculated-label {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.calculated-value {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(90deg, #7c9eff, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 5px;
}

.countdown-box {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    padding: 16px 22px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow:
        0 8px 32px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.countdown-label { color: rgba(255,255,255,0.6); font-size: 0.9rem; }
.countdown-value {
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #7c9eff, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ============================================================
   CHECKBOXES (habits)
   ============================================================ */

div[data-testid="stCheckbox"] {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 8px 12px;
    margin-bottom: 6px;
    transition: 0.2s ease;
}

div[data-testid="stCheckbox"]:hover {
    border-color: rgba(124, 158, 255, 0.3);
    background: rgba(124, 158, 255, 0.06);
}

/* ============================================================
   METRICS
   ============================================================ */

[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    padding: 18px 16px;
    box-shadow:
        0 8px 28px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(124, 158, 255, 0.25);
}
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.55); font-size: 0.85rem; }
[data-testid="stMetricValue"] { color: #f5f6fa; font-weight: 700; }

/* ============================================================
   TABS
   ============================================================ */

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(14px);
    border-radius: 14px;
    padding: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 10px;
    padding: 8px 18px;
    color: rgba(255,255,255,0.55);
    transition: 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(255,255,255,0.05);
    color: #f5f6fa;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(124,158,255,0.35), rgba(167,139,250,0.35));
    color: #ffffff !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.15);
}

/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {
    background: rgba(5, 5, 10, 0.55);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* ============================================================
   DATAFRAMES / DATA EDITOR
   ============================================================ */

div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.10);
}

/* ============================================================
   MISC
   ============================================================ */

.app-footer {
    text-align: center;
    color: rgba(255,255,255,0.3);
    font-size: 12px;
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

hr {
    border-color: rgba(255, 255, 255, 0.08) !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SHARED HELPERS
# ============================================================

def section_header(title, description):
    html = f"""
<div class="section-header">
    <div class="section-title">{title}</div>
    <div class="section-description">{description}</div>
</div>
"""
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)


def calculate_sleep_hours(sleep_time_value, wake_time_value):
    sleep_datetime = datetime.combine(date.today(), sleep_time_value)
    wake_datetime = datetime.combine(date.today(), wake_time_value)

    if wake_datetime <= sleep_datetime:
        wake_datetime += timedelta(days=1)

    duration = wake_datetime - sleep_datetime
    return round(duration.total_seconds() / 3600, 2)


def g(d, *keys, default=None):
    """Safe nested dict getter: g(existing_log, 'body', 'weight', default=91.0)"""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


CHART_TEMPLATE = "plotly_dark"
ACCENT = "#7c9eff"
ACCENT2 = "#a78bfa"

# Values in the "Workout" field that count as a rest day (rather than a training day)
REST_DAY_VALUES = {"rest", "rest day"}


def is_rest_day(workout_title):
    if pd.isna(workout_title):
        return True
    return str(workout_title).strip().lower() in REST_DAY_VALUES


def style_fig(fig):
    fig.update_layout(
        template=CHART_TEMPLATE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color="#e5e7eb"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#20222e")
    return fig


def compute_streaks(frame, cols):
    """Return {habit: {'current': n, 'longest': m}} computed over the given (already sorted-by-date) frame."""
    frame = frame.sort_values("Date")
    results = {}
    for col in cols:
        vals = frame[col].fillna(False).tolist()

        longest = 0
        running = 0
        for v in vals:
            running = running + 1 if v else 0
            longest = max(longest, running)

        current = 0
        for v in reversed(vals):
            if v:
                current += 1
            else:
                break

        results[col] = {"current": current, "longest": longest}
    return results


_SET_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|lbs?|lb)?\s*[x×]\s*(\d+)", re.IGNORECASE)


def parse_workout_sets(notes):
    """Parse freeform workout notes into (exercise_name, weight, reps) tuples.

    Expects a loose format like:
        Bench Press
        60 x 8
        70 x 6
    A line is treated as an exercise name if it doesn't match the '<weight> x <reps>' pattern.
    """
    if not notes or not isinstance(notes, str):
        return []

    results = []
    current_exercise = None
    for raw_line in notes.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _SET_PATTERN.search(line)
        if match:
            if current_exercise:
                weight = float(match.group(1))
                reps = int(match.group(2))
                results.append((current_exercise, weight, reps))
        else:
            current_exercise = line.strip(":").strip()
    return results


def generate_weekly_excel(frame):
    """Build a weekly Excel report (Mon-Sun week containing the most recent log) and return raw XLSX bytes.

    Produces a workbook with three sheets: Summary, Daily Log, and Habits.
    The week is always a full Monday-to-Sunday calendar week — specifically the
    week that contains the most recent logged date in `frame` — regardless of
    how many days within that week actually have entries.
    The "Daily Log" sheet includes every column present in the dataset (same
    columns as the full "Export to Excel" button), not a curated subset.
    """
    frame = frame.sort_values("Date")

    if frame.empty:
        last_date = pd.Timestamp(date.today())
    else:
        last_date = frame["Date"].max()

    # Monday-Sunday week containing the most recent logged date.
    # weekday(): Monday=0 ... Sunday=6
    week_start = last_date - pd.Timedelta(days=last_date.weekday())
    week_end = week_start + pd.Timedelta(days=6)

    week_df = frame[(frame["Date"] >= week_start) & (frame["Date"] <= week_end)].copy()

    gym_days = int(week_df["Gym Completed"].fillna(False).sum()) if not week_df.empty else 0
    rest_days = int(week_df["Workout"].apply(is_rest_day).sum()) if not week_df.empty else 0

    summary_df = pd.DataFrame({
        "Metric": [
            "Week",
            "Days Logged",
            "Avg Weight (kg)",
            "Avg Sleep (hrs)",
            "Avg Sleep Quality (/10)",
            "Avg Steps",
            "Avg Walking (km)",
            "Avg Exercise (min)",
            "Avg Water (L)",
            "Avg Mood (/10)",
            "Avg Happiness (/10)",
            "Avg Energy (/10)",
            "Avg Stress (/10)",
            "Avg Workout Rating (/10)",
            "Gym Days",
            "Rest Days",
        ],
        "Value": [
            f"{week_start.strftime('%d %b %Y')} - {week_end.strftime('%d %b %Y')} (Mon-Sun)",
            len(week_df),
            round(week_df["Weight"].mean(), 1) if week_df["Weight"].notna().any() else None,
            round(week_df["Sleep Hours"].mean(), 2) if week_df["Sleep Hours"].notna().any() else None,
            round(week_df["Sleep Quality"].mean(), 1) if week_df["Sleep Quality"].notna().any() else None,
            round(week_df["Steps"].mean(), 0) if week_df["Steps"].notna().any() else None,
            round(week_df["Walking KM"].mean(), 1) if week_df["Walking KM"].notna().any() else None,
            round(week_df["Exercise Minutes"].mean(), 0) if week_df["Exercise Minutes"].notna().any() else None,
            round(week_df["Water Litres"].mean(), 1) if week_df["Water Litres"].notna().any() else None,
            round(week_df["Mood"].mean(), 1) if week_df["Mood"].notna().any() else None,
            round(week_df["Happiness"].mean(), 1) if week_df["Happiness"].notna().any() else None,
            round(week_df["Energy"].mean(), 1) if week_df["Energy"].notna().any() else None,
            round(week_df["Stress"].mean(), 1) if week_df["Stress"].notna().any() else None,
            round(week_df["Workout Rating"].mean(), 1) if week_df["Workout Rating"].notna().any() else None,
            gym_days,
            rest_days,
        ],
    })

    # Daily Log sheet: every column present in the dataset (mirrors the full export)
    daily_log_df = week_df.sort_values("Date").copy()
    if "Date" in daily_log_df.columns and not daily_log_df.empty:
        daily_log_df["Date"] = daily_log_df["Date"].dt.strftime("%d %b %Y")

    habit_cols_local = [
        "Gym Completed", "Creatine", "Whey Protein", "Flaxseed",
        "8000 Steps", "Sleep Before 1 AM", "3L Water", "No Junk Food",
    ]
    habit_names, habit_pcts = [], []
    for col in habit_cols_local:
        if col in week_df.columns:
            habit_names.append(col)
            pct = round(week_df[col].fillna(False).mean() * 100, 0) if len(week_df) else 0
            habit_pcts.append(pct)
    habits_df = pd.DataFrame({"Habit": habit_names, "Completion %": habit_pcts})

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        daily_log_df.to_excel(writer, index=False, sheet_name="Daily Log")
        habits_df.to_excel(writer, index=False, sheet_name="Habits")

        from openpyxl.styles import Font

        for sheet_name, sheet_df in (
            ("Summary", summary_df),
            ("Daily Log", daily_log_df),
            ("Habits", habits_df),
        ):
            ws = writer.sheets[sheet_name]
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for i, col in enumerate(sheet_df.columns, start=1):
                if sheet_df.empty:
                    max_content_len = 0
                else:
                    max_content_len = max(len(str(v)) for v in sheet_df[col].tolist())
                max_len = max(max_content_len, len(col)) + 2
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max_len

    return output.getvalue()


@st.cache_data(ttl=300)
def load_dashboard_data():
    docs = list(daily_logs_collection.find({}, {"_id": 0}))
    rows = []
    for d in docs:
        sleep = d.get("sleep", {}) or {}
        body = d.get("body", {}) or {}
        mental = d.get("mental", {}) or {}
        activity = d.get("activity", {}) or {}
        workout = d.get("workout", {}) or {}
        habits = d.get("habits", {}) or {}

        rows.append({
            "Date": pd.to_datetime(d.get("date")),

            "Sleep Time": sleep.get("sleep_time"),
            "Wake Time": sleep.get("wake_time"),
            "Sleep Hours": sleep.get("sleep_hours"),
            "Sleep Quality": sleep.get("sleep_quality"),

            "Weight": body.get("weight"),

            "Mood": mental.get("mood"),
            "Happiness": mental.get("happiness"),
            "Energy": mental.get("energy"),
            "Stress": mental.get("stress"),

            "Steps": activity.get("steps"),
            "Walking KM": activity.get("walking_km"),
            "Exercise Minutes": activity.get("exercise_minutes"),
            "Water Litres": activity.get("water_litres"),

            "Workout": workout.get("title"),
            "Workout Notes": workout.get("notes"),
            "Workout Duration (min)": workout.get("duration_minutes"),
            "Workout Rating": workout.get("rating"),

            "Daily Notes": d.get("daily_notes", ""),

            "Gym Completed": habits.get("gym", False),
            "Creatine": habits.get("creatine", False),
            "Whey Protein": habits.get("whey", False),
            "Flaxseed": habits.get("flaxseed", False),
            "8000 Steps": habits.get("steps_8000", False),
            "Sleep Before 1 AM": habits.get("sleep_before_1", False),
            "3L Water": habits.get("water_3l", False),
            "No Junk Food": habits.get("no_junk_food", False),
        })
    return pd.DataFrame(rows).sort_values("Date")


# ============================================================
# TOP-LEVEL NAVIGATION
# ============================================================


tab_log, tab_dashboard = st.tabs(["📝 Daily Log", "📊 Dashboard"])


# ============================================================
# TAB 1 — DAILY LOG ENTRY
# ============================================================

with tab_log:

    if st.session_state.get("show_save_balloons"):
        st.balloons()
        del st.session_state["show_save_balloons"]

    header_left, header_right = st.columns([4, 1])

    with header_left:
        header_html = """
<div class="main-header">
    <div class="main-title">Daily Fitness Log</div>
    <div class="main-subtitle">Track health, training and lifestyle performance.</div>
    <div class="blue-line"></div>
</div>
"""
        st.markdown(dedent(header_html).strip(), unsafe_allow_html=True)

    with header_right:
        st.write("")
        if mongo_connected:
            st.markdown(
                '<div style="text-align: right; padding-top: 10px;">'
                '<span class="database-online">● DATABASE ONLINE</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align: right; padding-top: 10px;">'
                '<span class="database-offline">● DATABASE OFFLINE</span></div>',
                unsafe_allow_html=True,
            )

    if not mongo_connected:
        st.error(f"MongoDB Connection Error: {mongo_error}")

    # ---------- DATE ----------
    section_header("📅 Log Date", "Select the date this fitness log belongs to. Pick a past date to edit it.")

    with st.container(border=True):
        selected_date = st.date_input(
            "Select Date",
            value=date.today(),
            max_value=date.today(),
            key="log_date_input",
        )

    log_date = datetime.combine(selected_date, datetime.min.time())

    existing_log = None
    if mongo_connected:
        existing_log = daily_logs_collection.find_one({"date": log_date})

    if existing_log:
        st.info(f"Editing existing log for {selected_date.strftime('%d %B %Y')}.")

    # ---------- SLEEP + BODY/MENTAL ----------
    left, right = st.columns(2, gap="medium")

    with left:
        section_header("😴 Sleep & Recovery", "Track sleep schedule and recovery quality.")

        with st.container(border=True):
            sleep_col, wake_col = st.columns(2)

            default_sleep_time = time(1, 30)
            default_wake_time = time(8, 30)
            if existing_log:
                try:
                    default_sleep_time = datetime.strptime(
                        g(existing_log, "sleep", "sleep_time", default="01:30"), "%H:%M"
                    ).time()
                    default_wake_time = datetime.strptime(
                        g(existing_log, "sleep", "wake_time", default="08:30"), "%H:%M"
                    ).time()
                except ValueError:
                    pass

            with sleep_col:
                sleep_time = st.time_input("Sleep Time", value=default_sleep_time)
            with wake_col:
                wake_time = st.time_input("Wake Up Time", value=default_wake_time)

            sleep_quality = st.slider(
                "Sleep Quality", min_value=0, max_value=10,
                value=g(existing_log, "sleep", "sleep_quality", default=0),
            )

            sleep_hours = calculate_sleep_hours(sleep_time, wake_time)

            sleep_html = f"""
<div class="calculated-box">
    <div class="calculated-label">Calculated Sleep Duration</div>
    <div class="calculated-value">{sleep_hours} Hours</div>
</div>
"""
            st.markdown(dedent(sleep_html).strip(), unsafe_allow_html=True)

    with right:
        section_header("⚖️ Body & Mind", "Record your physical and mental state.")

        with st.container(border=True):
            weight = st.number_input(
                "Body Weight (KG)", min_value=0.0, max_value=250.0,
                value=float(g(existing_log, "body", "weight", default=0.0)), step=0.1,
            )

            mood_col, happiness_col = st.columns(2)
            with mood_col:
                mood = st.slider("Mood", 0, 10, g(existing_log, "mental", "mood", default=0))
            with happiness_col:
                happiness = st.slider("Happiness", 0, 10, g(existing_log, "mental", "happiness", default=0))

            energy_col, stress_col = st.columns(2)
            with energy_col:
                energy = st.slider("Energy", 0, 10, g(existing_log, "mental", "energy", default=0))
            with stress_col:
                stress = st.slider("Stress", 0, 10, g(existing_log, "mental", "stress", default=0))

    # ---------- DAILY ACTIVITY ----------
    section_header("🚶 Daily Activity", "Track steps, walking distance, exercise time and hydration.")

    with st.container(border=True):
        act_col1, act_col2, act_col3, act_col4 = st.columns(4)

        with act_col1:
            steps = st.number_input(
                "Steps", min_value=0,
                value=int(g(existing_log, "activity", "steps", default=0)), step=100,
            )
        with act_col2:
            walking_km = st.number_input(
                "Walking Distance (KM)", min_value=0.0,
                value=float(g(existing_log, "activity", "walking_km", default=0.0)), step=0.1,
            )
        with act_col3:
            exercise_minutes = st.number_input(
                "Exercise Minutes", min_value=0,
                value=int(g(existing_log, "activity", "exercise_minutes", default=0)), step=5,
            )
        with act_col4:
            water = st.number_input(
                "Water Intake (Litres)", min_value=0.0,
                value=float(g(existing_log, "activity", "water_litres", default=0.0)), step=0.1,
            )

    # ---------- WORKOUT ----------
    section_header("🏋️ Today's Workout", "Free typing. No dropdowns — describe your session however you like.")

    with st.container(border=True):
        workout_options = [
            "Running", "Rest", "Chest + Triceps", "Back + Biceps",
            "Bicep + Triceps", "Shoulders", "Others",
        ]

        existing_title = g(existing_log, "workout", "title", default="")
        title_lookup = {opt.lower(): opt for opt in workout_options}
        matched_option = title_lookup.get(existing_title.strip().lower())

        if matched_option:
            default_index = workout_options.index(matched_option)
            custom_default = ""
        elif existing_title:
            default_index = workout_options.index("Others")
            custom_default = existing_title
        else:
            default_index = 0
            custom_default = ""

        workout_choice = st.selectbox(
            "Workout Title",
            options=workout_options,
            index=default_index,
        )

        if workout_choice == "Others":
            workout_title = st.text_input(
                "Custom Workout Title",
                value=custom_default,
                placeholder="Type your own workout name",
            )
        else:
            workout_title = workout_choice

        workout_notes = st.text_area(
            "Workout Notes",
            value=g(existing_log, "workout", "notes", default=""),
            height=320,
            placeholder=(
                "Bench Press\n\n"
                "40 x 12\n50 x 10\n60 x 8\n\n"
                "Incline DB Press\n\n"
                "20 x 12\n22.5 x 10\n25 x 8\n\n"
                "Cable Fly\n\n"
                "15 x 15\n20 x 12\n\n"
                "Felt stronger today."
            ),
        )

        dur_col, rating_col = st.columns(2)
        with dur_col:
            workout_duration = st.number_input(
                "Workout Duration (Minutes)", min_value=0,
                value=int(g(existing_log, "workout", "duration_minutes", default=0)), step=5,
            )
        with rating_col:
            workout_rating = st.slider(
                "Workout Rating", min_value=0, max_value=10,
                value=g(existing_log, "workout", "rating", default=0),
            )

    # ---------- DAILY NOTES ----------
    section_header("📝 Daily Notes", "Anything else worth remembering about today.")

    with st.container(border=True):
        daily_notes = st.text_area(
            "Notes",
            value=g(existing_log, "daily_notes", default=""),
            height=160,
            placeholder="Busy day.\n\nShoulder slightly sore.\n\nNeed more sleep.\n\nGood pump.",
            label_visibility="collapsed",
        )

    # ---------- HABITS ----------
    section_header("✅ Habits", "Daily checklist.")

    with st.container(border=True):
        habit_col1, habit_col2 = st.columns(2)

        existing_habits = g(existing_log, "habits", default={}) or {}

        with habit_col1:
            gym_habit = st.checkbox("Gym Completed", value=existing_habits.get("gym", False))
            creatine_habit = st.checkbox("Creatine", value=existing_habits.get("creatine", False))
            whey_habit = st.checkbox("Whey Protein", value=existing_habits.get("whey", False))
            flaxseed_habit = st.checkbox("Flaxseed", value=existing_habits.get("flaxseed", False))

        with habit_col2:
            steps_habit = st.checkbox("8,000 Steps", value=existing_habits.get("steps_8000", False))
            sleep_habit = st.checkbox("Sleep Before 1 AM", value=existing_habits.get("sleep_before_1", False))
            water_habit = st.checkbox("3L Water", value=existing_habits.get("water_3l", False))
            junk_habit = st.checkbox("No Junk Food", value=existing_habits.get("no_junk_food", False))

    # ---------- SAVE / DELETE ----------
    st.write("")
    st.write("")

    save_left, save_center, save_right = st.columns([1, 2, 1])
    with save_center:
        save = st.button("SAVE DAILY LOG", width='stretch')

    if save:
        if not mongo_connected:
            st.error("Cannot save because MongoDB is offline.")
        else:
            log_date = datetime.combine(selected_date, datetime.min.time())

            daily_data = {
                "date": log_date,

                "sleep": {
                    "sleep_time": sleep_time.strftime("%H:%M"),
                    "wake_time": wake_time.strftime("%H:%M"),
                    "sleep_hours": sleep_hours,
                    "sleep_quality": sleep_quality,
                },

                "body": {"weight": weight},

                "mental": {
                    "mood": mood,
                    "happiness": happiness,
                    "energy": energy,
                    "stress": stress,
                },

                "activity": {
                    "steps": steps,
                    "walking_km": walking_km,
                    "exercise_minutes": exercise_minutes,
                    "water_litres": water,
                },

                "workout": {
                    "title": workout_title,
                    "notes": workout_notes,
                    "duration_minutes": workout_duration,
                    "rating": workout_rating,
                },

                "daily_notes": daily_notes,

                "habits": {
                    "gym": gym_habit,
                    "whey": whey_habit,
                    "steps_8000": steps_habit,
                    "sleep_before_1": sleep_habit,
                    "creatine": creatine_habit,
                    "flaxseed": flaxseed_habit,
                    "water_3l": water_habit,
                    "no_junk_food": junk_habit,
                },

                "updated_at": datetime.now(),
            }

            try:
                result = daily_logs_collection.update_one(
                    {"date": log_date},
                    {
                        "$set": daily_data,
                        "$setOnInsert": {"created_at": datetime.now()},
                    },
                    upsert=True,
                )

                if result.upserted_id:
                    st.success(f"New fitness log created for {selected_date.strftime('%d %B %Y')}")
                else:
                    st.success(f"Fitness log updated for {selected_date.strftime('%d %B %Y')}")

                load_dashboard_data.clear()  # refresh dashboard cache with the new save

                st.session_state["show_save_balloons"] = True
                st.rerun()

            except Exception as error:
                st.error(f"MongoDB Save Error: {error}")

    # ---------- DELETE THIS DAY ----------
    if mongo_connected and existing_log:
        st.write("")
        with st.expander("🗑️ Delete this day's log"):
            st.warning(
                f"This will permanently delete the log for "
                f"**{selected_date.strftime('%d %B %Y')}**. This cannot be undone."
            )
            confirm_delete = st.checkbox(
                "I understand this cannot be undone", key="confirm_delete_day"
            )
            del_left, del_center, del_right = st.columns([1, 2, 1])
            with del_center:
                delete_clicked = st.button(
                    "DELETE THIS DAY",
                    width='stretch',
                    disabled=not confirm_delete,
                    key="delete_day_button",
                )
            if delete_clicked:
                try:
                    daily_logs_collection.delete_one({"date": log_date})
                    load_dashboard_data.clear()
                    st.session_state["show_delete_success"] = selected_date.strftime('%d %B %Y')
                    st.rerun()
                except Exception as error:
                    st.error(f"MongoDB Delete Error: {error}")

    if st.session_state.get("show_delete_success"):
        st.success(f"Deleted the log for {st.session_state['show_delete_success']}.")
        del st.session_state["show_delete_success"]

    st.markdown(
        '<div class="app-footer">FITGRAPH · PERSONAL FITNESS INTELLIGENCE SYSTEM</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# TAB 2 — DASHBOARD
# ============================================================

with tab_dashboard:

    if st.session_state.get("dashboard_success_message"):
        st.success(st.session_state["dashboard_success_message"])
        del st.session_state["dashboard_success_message"]
    if st.session_state.get("show_dashboard_balloons"):
        st.balloons()
        del st.session_state["show_dashboard_balloons"]

    df = load_dashboard_data()

    if not df.empty:
        full_range = pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")
        df = df.set_index("Date").reindex(full_range).rename_axis("Date").reset_index()
        df["Workout"] = df["Workout"].fillna("Rest Day")
        habit_cols_all = [
            "Gym Completed", "Creatine", "Whey Protein", "Flaxseed",
            "8000 Steps", "Sleep Before 1 AM", "3L Water", "No Junk Food",
        ]
        for col in habit_cols_all:
            df[col] = df[col].fillna(False)

    st.markdown('<div class="dash-title">📊 Fitness Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">Weight · Sleep · Steps · Mood · Workout log</div>', unsafe_allow_html=True)

    # ---------- COUNTDOWN ----------
    today = date.today()
    target_date = date(today.year, 9, 26)
    if target_date < today:
        target_date = date(today.year + 1, 9, 26)

    days_left = (target_date - today).days

    if days_left == 0:
        countdown_text = "Today! ✈️"
    elif days_left == 1:
        countdown_text = "1 day left"
    else:
        countdown_text = f"{days_left} days left"

    st.markdown(
        f"""
        <div class="countdown-box">
            <div class="countdown-label">✈️ Countdown to {target_date.strftime('%d %B %Y')}</div>
            <div class="countdown-value">{countdown_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.warning("No data found.")
        st.stop()

    # ---------- FILTERS ----------
    with st.sidebar:
        st.header("Filters")
        min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
        date_range = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)

        workouts = sorted(df["Workout"].dropna().unique().tolist())
        selected_workouts = st.multiselect("Workout type", options=workouts, default=workouts)

        st.markdown("---")
        st.caption(f"{len(df)} total logged days")

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df = df[(df["Date"] >= start) & (df["Date"] <= end)]

    if selected_workouts:
        df = df[df["Workout"].isin(selected_workouts) | df["Workout"].isna()]

    if df.empty:
        st.info("No data in the selected range/filters.")
        st.stop()

    df = df.sort_values("Date")

    # ---------- METRICS ----------
    def delta(series):
        s = series.dropna()
        if len(s) < 2:
            return None
        return round(s.iloc[-1] - s.iloc[-2], 2)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Weight", f"{df['Weight'].dropna().iloc[-1]:.1f} kg", delta=delta(df["Weight"]))
    c2.metric("Avg Sleep", f"{df['Sleep Hours'].mean():.2f} hrs", delta=delta(df["Sleep Hours"]))
    c3.metric("Avg Steps", f"{df['Steps'].mean():,.0f}", delta=delta(df["Steps"]))
    c4.metric("Avg Mood", f"{df['Mood'].mean():.1f}/10", delta=delta(df["Mood"]))

    # Gym days vs rest days — current calendar month only (independent of the sidebar date filter)
    month_start = pd.Timestamp(today.year, today.month, 1)
    month_df = df[(df["Date"] >= month_start) & (df["Date"].dt.month == today.month) & (df["Date"].dt.year == today.year)]

    gym_days_count = int(month_df["Gym Completed"].fillna(False).sum())
    rest_days_count = int(month_df["Workout"].apply(is_rest_day).sum())
    total_days_count = len(month_df)

    c5, c6 = st.columns(2)
    c5.metric(
        "🏋️ Gym Days",
        f"{gym_days_count} / {total_days_count}",
        help="Days this calendar month where 'Gym Completed' habit was checked.",
    )
    c6.metric(
        "🛌 Rest Days",
        f"{rest_days_count} / {total_days_count}",
        help="Days this calendar month logged as 'Rest' (or with no workout logged).",
    )

    st.write("")

    # ---------- TABS ----------
    tab_weight, tab_sleep, tab_steps, tab_mood, tab_habits, tab_history = st.tabs(
        ["⚖️ Weight", "😴 Sleep", "👟 Steps", "🙂 Mood", "✅ Habits & Extras", "🏋️ History"]
    )

    with tab_weight:
        weight_df = df[["Date", "Weight"]].dropna(subset=["Weight"]).sort_values("Date")
        weight_df["7-day avg"] = weight_df["Weight"].rolling(7, min_periods=1).mean()

        fig = px.line(weight_df, x="Date", y="Weight", markers=True, color_discrete_sequence=[ACCENT])
        fig.update_traces(fill="tozeroy", fillcolor="rgba(124,158,255,0.08)", name="Weight")
        fig.add_scatter(
            x=weight_df["Date"], y=weight_df["7-day avg"],
            mode="lines", name="7-day avg",
            line=dict(color=ACCENT2, width=3, dash="dash"),
        )
        fig.update_layout(showlegend=True)
        st.plotly_chart(style_fig(fig), width='stretch')

    with tab_sleep:
        fig = px.line(df, x="Date", y="Sleep Hours", markers=True, color_discrete_sequence=[ACCENT2])
        fig.add_hline(y=8, line_dash="dot", line_color="#4b5563", annotation_text="target: 8h")
        st.plotly_chart(style_fig(fig), width='stretch')

    with tab_steps:
        fig = px.bar(df, x="Date", y="Steps", color_discrete_sequence=[ACCENT])
        st.plotly_chart(style_fig(fig), width='stretch')

    with tab_mood:
        fig = px.line(df, x="Date", y="Mood", markers=True, color_discrete_sequence=["#34d399"])
        fig.update_yaxes(range=[0, 10])
        st.plotly_chart(style_fig(fig), width='stretch')

    with tab_habits:
        habit_cols = [
            "Gym Completed", "Creatine", "Whey Protein", "Flaxseed",
            "8000 Steps", "Sleep Before 1 AM", "3L Water", "No Junk Food",
        ]

        st.markdown("**🔥 Streaks**")
        streaks = compute_streaks(df, habit_cols)
        streak_rows = [habit_cols[i:i + 4] for i in range(0, len(habit_cols), 4)]
        for row_cols in streak_rows:
            cols = st.columns(len(row_cols))
            for c, habit in zip(cols, row_cols):
                s = streaks[habit]
                c.metric(habit, f"{s['current']}🔥", help=f"Longest streak: {s['longest']} days")

        st.markdown("**Habit completion rate**")
        rates = (df[habit_cols].fillna(False).mean() * 100).round(0).sort_values(ascending=False)
        fig = px.bar(
            x=rates.values, y=rates.index, orientation="h",
            labels={"x": "% of days completed", "y": ""},
            color_discrete_sequence=[ACCENT],
        )
        st.plotly_chart(style_fig(fig), width='stretch')

        st.markdown("**Mental health & activity extras**")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Avg Happiness", f"{df['Happiness'].mean():.1f}/10")
        e2.metric("Avg Energy", f"{df['Energy'].mean():.1f}/10")
        e3.metric("Avg Stress", f"{df['Stress'].mean():.1f}/10")
        e4.metric("Avg Sleep Quality", f"{df['Sleep Quality'].mean():.1f}/10")

        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Avg Walking", f"{df['Walking KM'].mean():.1f} km")
        f2.metric("Avg Exercise", f"{df['Exercise Minutes'].mean():.0f} min")
        f3.metric("Avg Water", f"{df['Water Litres'].mean():.1f} L")
        f4.metric("Avg Workout Rating", f"{df['Workout Rating'].mean():.1f}/10")

        st.markdown("**Daily habit log** — edit checkboxes directly, then save.")
        habit_table = df[["Date"] + habit_cols].sort_values("Date", ascending=False).reset_index(drop=True)

        edited_habits = st.data_editor(
            habit_table,
            width='stretch',
            hide_index=True,
            disabled=["Date"],
            column_config={
                col: st.column_config.CheckboxColumn(col) for col in habit_cols
            },
            key="habit_editor",
        )

        if st.button("💾 Save Habit Changes", width='stretch'):
            updated_count = 0
            for _, row in edited_habits.iterrows():
                row_date = pd.to_datetime(row["Date"])
                log_dt = datetime.combine(row_date.date(), datetime.min.time())
                habits_payload = {
                    "gym": bool(row["Gym Completed"]),
                    "creatine": bool(row["Creatine"]),
                    "whey": bool(row["Whey Protein"]),
                    "flaxseed": bool(row["Flaxseed"]),
                    "steps_8000": bool(row["8000 Steps"]),
                    "sleep_before_1": bool(row["Sleep Before 1 AM"]),
                    "water_3l": bool(row["3L Water"]),
                    "no_junk_food": bool(row["No Junk Food"]),
                }
                daily_logs_collection.update_one(
                    {"date": log_dt},
                    {
                        "$set": {"habits": habits_payload, "updated_at": datetime.now()},
                        "$setOnInsert": {"date": log_dt, "created_at": datetime.now()},
                    },
                    upsert=True,
                )
                updated_count += 1

            load_dashboard_data.clear()
            st.session_state["dashboard_success_message"] = f"Updated habits for {updated_count} day(s)."
            st.session_state["show_dashboard_balloons"] = True
            st.rerun()

    with tab_history:
        for _, r in df.sort_values("Date", ascending=False).iterrows():
            title = r["Workout"] if pd.notna(r["Workout"]) else "Rest Day"
            with st.expander(f"{r['Date'].strftime('%d %b %Y')} — {title}"):
                if title == "Rest Day" and pd.isna(r.get("Weight")):
                    st.caption("No log entry for this day.")
                    continue
                meta_bits = []
                if pd.notna(r["Workout Duration (min)"]):
                    meta_bits.append(f"⏱ {r['Workout Duration (min)']:.0f} min")
                if pd.notna(r["Workout Rating"]):
                    meta_bits.append(f"⭐ {r['Workout Rating']:.0f}/10")
                if meta_bits:
                    st.caption(" · ".join(meta_bits))
                if r["Workout Notes"]:
                    st.code(r["Workout Notes"])
                if r["Daily Notes"]:
                    st.write(r["Daily Notes"])

    # ---------- EXPORT ----------
    st.markdown("---")
    st.subheader("📥 Export Data")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Daily Logs")

    st.download_button(
        label="⬇ Export to Excel",
        data=output.getvalue(),
        file_name="fitness_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch',
    )

    # ---------- WEEKLY EXCEL REPORT ----------
    st.markdown("---")
    st.subheader("📄 Weekly Excel Report")
    st.caption(
        "A workbook summarizing the current Monday–Sunday week (the week containing "
        "your most recent log) — weight, sleep, mood, steps, workouts, gym/rest day "
        "counts, and habit completion, split across three sheets (Summary, Daily Log, "
        "Habits). The Daily Log sheet includes every column, same as the full export."
    )

    weekly_excel_bytes = generate_weekly_excel(df)
    st.download_button(
        label="⬇ Download Weekly Excel Report",
        data=weekly_excel_bytes,
        file_name="fitgraph_weekly_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch',
    )

    # ---------- IMPORT ----------
    st.markdown("---")
    st.subheader("📤 Import Data")
    st.caption(
        "Edit the exported Excel file (weight, sleep, mood, workout notes, habits, etc.) "
        "then upload it here. Each row is matched by Date and upserted into MongoDB — "
        "existing days get overwritten with the new values, new dates get created."
    )

    uploaded_file = st.file_uploader("Choose the edited Excel file", type=["xlsx"], key="import_file")

    if uploaded_file is not None:
        try:
            import_df = pd.read_excel(uploaded_file)
        except Exception as e:
            import_df = None
            st.error(f"Could not read file: {e}")

        if import_df is not None:
            if "Date" not in import_df.columns:
                st.error("This file doesn't have a 'Date' column — make sure you're uploading the exported file.")
            else:
                st.write(f"Found **{len(import_df)}** rows in the uploaded file. Preview:")
                st.dataframe(import_df.head(10), width='stretch', hide_index=True)

                confirm_import = st.checkbox(
                    "I've reviewed this data and want to overwrite matching dates in MongoDB"
                )

                if st.button("⬆ Import & Save to MongoDB", width='stretch', disabled=not confirm_import):

                    def safe_str(v, default=""):
                        return default if pd.isna(v) else str(v)

                    def safe_float(v, default=0.0):
                        try:
                            return default if pd.isna(v) else float(v)
                        except (TypeError, ValueError):
                            return default

                    def safe_int(v, default=0):
                        try:
                            return default if pd.isna(v) else int(v)
                        except (TypeError, ValueError):
                            return default

                    def safe_bool(v):
                        if pd.isna(v):
                            return False
                        if isinstance(v, str):
                            return v.strip().lower() in ("true", "1", "yes")
                        return bool(v)

                    imported, skipped = 0, 0

                    for _, row in import_df.iterrows():
                        try:
                            row_date = pd.to_datetime(row.get("Date"))
                            if pd.isna(row_date):
                                skipped += 1
                                continue

                            # Skip auto-filled "Rest Day" placeholder rows that never had real data
                            is_blank_rest_day = (
                                str(row.get("Workout", "")).strip().lower() == "rest day"
                                and pd.isna(row.get("Weight"))
                                and pd.isna(row.get("Sleep Hours"))
                                and pd.isna(row.get("Steps"))
                            )
                            if is_blank_rest_day:
                                skipped += 1
                                continue

                            log_dt = datetime.combine(row_date.date(), datetime.min.time())

                            daily_data = {
                                "date": log_dt,
                                "sleep": {
                                    "sleep_time": safe_str(row.get("Sleep Time")),
                                    "wake_time": safe_str(row.get("Wake Time")),
                                    "sleep_hours": safe_float(row.get("Sleep Hours")),
                                    "sleep_quality": safe_int(row.get("Sleep Quality")),
                                },
                                "body": {"weight": safe_float(row.get("Weight"))},
                                "mental": {
                                    "mood": safe_int(row.get("Mood")),
                                    "happiness": safe_int(row.get("Happiness")),
                                    "energy": safe_int(row.get("Energy")),
                                    "stress": safe_int(row.get("Stress")),
                                },
                                "activity": {
                                    "steps": safe_int(row.get("Steps")),
                                    "walking_km": safe_float(row.get("Walking KM")),
                                    "exercise_minutes": safe_int(row.get("Exercise Minutes")),
                                    "water_litres": safe_float(row.get("Water Litres")),
                                },
                                "workout": {
                                    "title": safe_str(row.get("Workout")),
                                    "notes": safe_str(row.get("Workout Notes")),
                                    "duration_minutes": safe_int(row.get("Workout Duration (min)")),
                                    "rating": safe_int(row.get("Workout Rating")),
                                },
                                "daily_notes": safe_str(row.get("Daily Notes")),
                                "habits": {
                                    "gym": safe_bool(row.get("Gym Completed")),
                                    "creatine": safe_bool(row.get("Creatine")),
                                    "whey": safe_bool(row.get("Whey Protein")),
                                    "flaxseed": safe_bool(row.get("Flaxseed")),
                                    "steps_8000": safe_bool(row.get("8000 Steps")),
                                    "sleep_before_1": safe_bool(row.get("Sleep Before 1 AM")),
                                    "water_3l": safe_bool(row.get("3L Water")),
                                    "no_junk_food": safe_bool(row.get("No Junk Food")),
                                },
                                "updated_at": datetime.now(),
                            }

                            daily_logs_collection.update_one(
                                {"date": log_dt},
                                {
                                    "$set": daily_data,
                                    "$setOnInsert": {"created_at": datetime.now()},
                                },
                                upsert=True,
                            )
                            imported += 1

                        except Exception:
                            skipped += 1

                    load_dashboard_data.clear()
                    st.session_state["dashboard_success_message"] = (
                        f"Imported {imported} row(s), skipped {skipped}."
                    )
                    st.session_state["show_dashboard_balloons"] = True
                    st.rerun()
