import os
import random
import time
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="AviaWake", page_icon=":airplane:")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
    h1 {
        font-family: 'Playfair Display', serif !important;
        font-weight: 700;
    }
    body {
        background: #f5f7fb;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: nowrap;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AviaWake")
st.caption("Pilot fatigue and readiness tracker")

CSV_PATH = "readiness_log.csv"


def load_history():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(
            columns=[
                "timestamp",
                "pilot_name",
                "sleep_hours",
                "reaction_ms",
                "orientation_accuracy",
                "memory_score",
                "readiness_score",
                "status",
                "notes",
            ]
        )

    df = pd.read_csv(CSV_PATH)
    return df


def save_history(df):
    df.to_csv(CSV_PATH, index=False)


def readiness_status(score):
    if score >= 80:
        return "Ready"
    if score >= 65:
        return "Monitor"
    return "Not recommended for duty"


def readiness_message(score):
    if score >= 80:
        return "Strong readiness. Maintain current workload and sleep quality."
    if score >= 65:
        return "Moderate readiness. Monitor fatigue and workload closely."
    return "Low readiness. Consider reducing workload or delaying demanding tasks."


def compute_readiness(sleep_hours, reaction_ms, orientation_accuracy, memory_score):
    sleep_component = max(0, min(100, (sleep_hours / 8) * 100))
    reaction_component = max(0, 100 - min(reaction_ms / 5, 100))
    orientation_component = orientation_accuracy * 100
    memory_component = memory_score
    score = round(
        (sleep_component * 0.25)
        + (reaction_component * 0.35)
        + (orientation_component * 0.2)
        + (memory_component * 0.2)
    )
    score = max(0, min(100, score))
    return score, readiness_status(score), readiness_message(score)


if "pilot_name" not in st.session_state:
    st.session_state.pilot_name = "Pilot 1"
if "notes" not in st.session_state:
    st.session_state.notes = ""
if "history_df" not in st.session_state:
    st.session_state.history_df = load_history()

st.session_state.pilot_name = st.text_input("Pilot name", value=st.session_state.pilot_name)
st.session_state.notes = st.text_area(
    "Notes",
    value=st.session_state.notes,
    placeholder="Late night, missed meal, stress, etc.",
)

sleep = st.slider("Hours slept last night", 0, 12, 8)
mission_phase = st.selectbox("Mission phase", ["Cruise", "Approach", "Taxi", "High workload"])

# Reaction test state
if "reaction_state" not in st.session_state:
    st.session_state.reaction_state = "idle"
if "reaction_ready_time" not in st.session_state:
    st.session_state.reaction_ready_time = None
if "reaction_start_time" not in st.session_state:
    st.session_state.reaction_start_time = None

# Orientation state
if "orientation_state" not in st.session_state:
    st.session_state.orientation_state = "idle"
if "orientation_target" not in st.session_state:
    st.session_state.orientation_target = 0
if "orientation_start_time" not in st.session_state:
    st.session_state.orientation_start_time = None
if "orientation_expected" not in st.session_state:
    st.session_state.orientation_expected = "left"
if "orientation_last_result" not in st.session_state:
    st.session_state.orientation_last_result = None

# Memory game state
if "memory_state" not in st.session_state:
    st.session_state.memory_state = "idle"
if "memory_sequence" not in st.session_state:
    st.session_state.memory_sequence = []
if "memory_guess" not in st.session_state:
    st.session_state.memory_guess = []
if "memory_started_at" not in st.session_state:
    st.session_state.memory_started_at = None
if "memory_last_result" not in st.session_state:
    st.session_state.memory_last_result = None

memory_icons = ["✈️", "🧭", "⏱️", "📡", "🌙", "⚙️", "🛰️", "🛬", "🛫", "⚡"]


def add_log_entry(entry):
    new_df = pd.DataFrame([entry])
    if st.session_state.history_df.empty:
        st.session_state.history_df = new_df
    else:
        st.session_state.history_df = pd.concat([st.session_state.history_df, new_df], ignore_index=True)
    save_history(st.session_state.history_df)


def latest_summary():
    df = st.session_state.history_df.copy()
    if df.empty:
        return {
            "sleep_hours": sleep,
            "reaction_ms": None,
            "orientation_accuracy": None,
            "memory_score": None,
        }

    latest_sleep = df["sleep_hours"].dropna().iloc[-1] if "sleep_hours" in df.columns and not df["sleep_hours"].dropna().empty else sleep
    latest_reaction = df["reaction_ms"].dropna().iloc[-1] if "reaction_ms" in df.columns and not df["reaction_ms"].dropna().empty else None
    latest_orientation = df["orientation_accuracy"].dropna().iloc[-1] if "orientation_accuracy" in df.columns and not df["orientation_accuracy"].dropna().empty else None
    latest_memory = df["memory_score"].dropna().iloc[-1] if "memory_score" in df.columns and not df["memory_score"].dropna().empty else None

    return {
        "sleep_hours": latest_sleep,
        "reaction_ms": latest_reaction,
        "orientation_accuracy": latest_orientation,
        "memory_score": latest_memory,
    }


def trend_summary(df):
    if df.empty:
        return "No data yet. Start a session to begin tracking.", None

    chart_df = df.copy()
    if "timestamp" in chart_df.columns:
        chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"], errors="coerce")
    else:
        chart_df["timestamp"] = pd.to_datetime(datetime.now())

    chart_df = chart_df.sort_values("timestamp")
    chart_df = chart_df.tail(7)

    if "readiness_score" in chart_df.columns:
        chart_df = chart_df.dropna(subset=["readiness_score"])
        if chart_df.empty:
            return "No trend data available yet.", None
        return "Recent trend", chart_df.set_index("timestamp")["readiness_score"]

    return "No trend data available yet.", None


with st.container():
    st.write("---")
    st.subheader("Overview")

    summary = latest_summary()
    if summary["reaction_ms"] is not None and summary["orientation_accuracy"] is not None and summary["memory_score"] is not None:
        score, status, message = compute_readiness(
            summary["sleep_hours"],
            summary["reaction_ms"],
            summary["orientation_accuracy"],
            summary["memory_score"],
        )
        st.metric("Overall readiness", f"{score}/100")
        st.metric("Status", status)
        st.success(message)
    else:
        st.info("Complete a reaction test, orientation drill, and memory challenge to see your readiness summary.")

    st.write("---")


tabs = st.tabs(["Dashboard", "Reaction", "Orientation", "Memory", "History"])

with tabs[0]:
    st.subheader("Dashboard")
    summary = latest_summary()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sleep", f"{summary['sleep_hours']}h")
    with col2:
        st.metric("Reaction", f"{summary['reaction_ms']} ms" if summary["reaction_ms"] is not None else "—")
    with col3:
        st.metric("Orientation", f"{int((summary['orientation_accuracy'] or 0) * 100)}%" if summary["orientation_accuracy"] is not None else "—")
    with col4:
        st.metric("Memory", f"{summary['memory_score']}%" if summary["memory_score"] is not None else "—")

    if summary["reaction_ms"] is not None and summary["orientation_accuracy"] is not None and summary["memory_score"] is not None:
        score, status, message = compute_readiness(
            summary["sleep_hours"],
            summary["reaction_ms"],
            summary["orientation_accuracy"],
            summary["memory_score"],
        )
        st.metric("Readiness score", f"{score}/100")
        st.metric("Readiness status", status)
        st.success(message)

    trend_text, trend_chart = trend_summary(st.session_state.history_df)
    st.write(trend_text)
    if trend_chart is not None:
        st.line_chart(trend_chart)

with tabs[1]:
    st.subheader("Reaction test")
    if st.button("Start reaction test", key="reaction_start", use_container_width=True):
        st.session_state.reaction_state = "waiting"
        st.session_state.reaction_ready_time = time.time() + random.uniform(2, 5)
        st.session_state.reaction_start_time = None

    if st.session_state.reaction_state == "waiting":
        if time.time() >= st.session_state.reaction_ready_time:
            st.session_state.reaction_state = "ready"
            st.session_state.reaction_start_time = time.time()
        else:
            st.info("Waiting for green...")

    if st.session_state.reaction_state == "ready":
        st.success("TAP NOW!")
        if st.button("Tap!", key="reaction_tap", use_container_width=True):
            reaction_ms = int((time.time() - st.session_state.reaction_start_time) * 1000)
            score, status, message = compute_readiness(sleep, reaction_ms, 1.0, 100)
            record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pilot_name": st.session_state.pilot_name,
                "sleep_hours": sleep,
                "reaction_ms": reaction_ms,
                "orientation_accuracy": None,
                "memory_score": None,
                "readiness_score": score,
                "status": status,
                "notes": st.session_state.notes,
            }
            add_log_entry(record)
            st.session_state.reaction_state = "complete"
            st.metric("Reaction time", f"{reaction_ms} ms")
            st.success(message)

    if st.session_state.reaction_state == "complete":
        st.write("Reaction test complete. View the dashboard for updated readiness.")

    if st.button("Reset reaction", key="reaction_reset", use_container_width=True):
        st.session_state.reaction_state = "idle"
        st.session_state.reaction_ready_time = None
        st.session_state.reaction_start_time = None

with tabs[2]:
    st.subheader("Orientation drill")
    if st.button("Start orientation drill", key="orientation_start", use_container_width=True):
        st.session_state.orientation_state = "showing"
        st.session_state.orientation_target = random.choice([-60, -45, -30, 30, 45, 60])
        st.session_state.orientation_start_time = time.time()
        st.session_state.orientation_expected = "left" if st.session_state.orientation_target < 0 else "right"
        st.session_state.orientation_last_result = None

    if st.session_state.orientation_state == "showing":
        tilt = st.session_state.orientation_target
        st.markdown(
            f"<div style='text-align:center; font-size:120px; transform: rotate({tilt}deg);'>✈️</div>",
            unsafe_allow_html=True,
        )
        st.write(f"Choose the direction that brings the aircraft back to level.")

        col_left, col_right = st.columns(2)
        with col_left:
            if st.button("LEFT", key="orientation_left", use_container_width=True):
                elapsed_ms = int((time.time() - st.session_state.orientation_start_time) * 1000)
                correct = 1 if st.session_state.orientation_expected == "left" else 0
                accuracy = correct
                score, status, message = compute_readiness(sleep, 250, accuracy, 100)
                record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "pilot_name": st.session_state.pilot_name,
                    "sleep_hours": sleep,
                    "reaction_ms": None,
                    "orientation_accuracy": accuracy,
                    "memory_score": None,
                    "readiness_score": score,
                    "status": status,
                    "notes": st.session_state.notes,
                }
                add_log_entry(record)
                st.session_state.orientation_last_result = {
                    "speed": elapsed_ms,
                    "accuracy": accuracy,
                    "message": message,
                }
                st.session_state.orientation_state = "result"

        with col_right:
            if st.button("RIGHT", key="orientation_right", use_container_width=True):
                elapsed_ms = int((time.time() - st.session_state.orientation_start_time) * 1000)
                correct = 1 if st.session_state.orientation_expected == "right" else 0
                accuracy = correct
                score, status, message = compute_readiness(sleep, 250, accuracy, 100)
                record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "pilot_name": st.session_state.pilot_name,
                    "sleep_hours": sleep,
                    "reaction_ms": None,
                    "orientation_accuracy": accuracy,
                    "memory_score": None,
                    "readiness_score": score,
                    "status": status,
                    "notes": st.session_state.notes,
                }
                add_log_entry(record)
                st.session_state.orientation_last_result = {
                    "speed": elapsed_ms,
                    "accuracy": accuracy,
                    "message": message,
                }
                st.session_state.orientation_state = "result"

    if st.session_state.orientation_state == "result":
        result = st.session_state.orientation_last_result
        if result:
            st.metric("Orientation speed", f"{result['speed']} ms")
            st.metric("Accuracy", f"{int(result['accuracy'] * 100)}%")
            if result["accuracy"] == 1:
                st.success("Correct. Good spatial awareness.")
            else:
                st.warning("Incorrect. Consider workload and fatigue management.")

    if st.button("Reset orientation", key="orientation_reset", use_container_width=True):
        st.session_state.orientation_state = "idle"
        st.session_state.orientation_target = 0
        st.session_state.orientation_start_time = None
        st.session_state.orientation_expected = "left"
        st.session_state.orientation_last_result = None

with tabs[3]:
    st.subheader("Memory challenge")
    if st.button("Start memory challenge", key="memory_start", use_container_width=True):
        sequence_length = random.randint(3, 5)
        st.session_state.memory_sequence = random.sample(memory_icons, sequence_length)
        st.session_state.memory_guess = []
        st.session_state.memory_started_at = time.time()
        st.session_state.memory_state = "showing"
        st.session_state.memory_last_result = None

    if st.session_state.memory_state == "showing":
        st.write("Memorize the pattern:")
        st.markdown(
            f"<div style='font-size:60px; text-align:center'> {' '.join(st.session_state.memory_sequence)} </div>",
            unsafe_allow_html=True,
        )
        if time.time() - st.session_state.memory_started_at >= 3:
            st.session_state.memory_state = "guessing"

    if st.session_state.memory_state == "guessing":
        st.write("Repeat the sequence in order:")
        st.write("Current guess: " + (" ".join(st.session_state.memory_guess) if st.session_state.memory_guess else "—"))

        cols = st.columns(5)
        for idx, icon in enumerate(memory_icons):
            with cols[idx % 5]:
                if st.button(icon, key=f"memory_icon_{idx}", use_container_width=True):
                    st.session_state.memory_guess.append(icon)
                    expected = st.session_state.memory_sequence[len(st.session_state.memory_guess) - 1]
                    if icon != expected:
                        score = 0
                        status = "Incorrect"
                        record = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "pilot_name": st.session_state.pilot_name,
                            "sleep_hours": sleep,
                            "reaction_ms": None,
                            "orientation_accuracy": None,
                            "memory_score": score,
                            "readiness_score": score,
                            "status": status,
                            "notes": st.session_state.notes,
                        }
                        add_log_entry(record)
                        st.session_state.memory_last_result = {"score": score, "passed": False}
                        st.session_state.memory_state = "result"
                    elif len(st.session_state.memory_guess) == len(st.session_state.memory_sequence):
                        score = 100
                        status = "Correct"
                        record = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "pilot_name": st.session_state.pilot_name,
                            "sleep_hours": sleep,
                            "reaction_ms": None,
                            "orientation_accuracy": None,
                            "memory_score": score,
                            "readiness_score": score,
                            "status": status,
                            "notes": st.session_state.notes,
                        }
                        add_log_entry(record)
                        st.session_state.memory_last_result = {"score": score, "passed": True}
                        st.session_state.memory_state = "result"

    if st.session_state.memory_state == "result":
        result = st.session_state.memory_last_result
        if result:
            if result["passed"]:
                st.success("Perfect memory. Sequence matched.")
            else:
                st.warning("Incorrect sequence. Try again.")
            st.metric("Memory score", f"{result['score']}%")

    if st.button("Reset memory", key="memory_reset", use_container_width=True):
        st.session_state.memory_state = "idle"
        st.session_state.memory_sequence = []
        st.session_state.memory_guess = []
        st.session_state.memory_started_at = None
        st.session_state.memory_last_result = None

with tabs[4]:
    st.subheader("History")
    df = st.session_state.history_df.copy()
    if df.empty:
        st.write("No entries yet.")
    else:
        st.dataframe(df.tail(20), use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download readiness log",
            data=csv,
            file_name="readiness_log.csv",
            mime="text/csv",
        )

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"])
            if not df.empty:
                trend = df.tail(7).copy()
                if "readiness_score" in trend.columns:
                    trend = trend.dropna(subset=["readiness_score"])
                    if not trend.empty:
                        st.line_chart(trend.set_index("timestamp")["readiness_score"])

st.write("---")
st.caption("AviaWake prototype")
