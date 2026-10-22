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
    .stMetric {
        background: #ffffff;
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AviaWake")
st.caption("Pilot Fatigue & Readiness Tracker")

CSV_PATH = "reaction_history.csv"


def calculate_readiness_score(sleep_hours, reaction_ms):
    sleep_component = max(0, min(100, (sleep_hours / 8) * 100))
    reaction_component = max(0, 100 - min(reaction_ms / 5, 100))
    score = round((sleep_component * 0.45) + (reaction_component * 0.55))

    if score >= 80:
        label = "Excellent"
    elif score >= 65:
        label = "Good"
    elif score >= 50:
        label = "Watch"
    else:
        label = "High fatigue risk"

    return score, label


if "reaction_state" not in st.session_state:
    st.session_state.reaction_state = "idle"
if "ready_time" not in st.session_state:
    st.session_state.ready_time = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "result_history" not in st.session_state:
    if os.path.exists(CSV_PATH):
        try:
            saved_df = pd.read_csv(CSV_PATH)
            if not saved_df.empty:
                st.session_state.result_history = saved_df.to_dict("records")
            else:
                st.session_state.result_history = []
        except Exception:
            st.session_state.result_history = []
    else:
        st.session_state.result_history = []

sleep = st.slider("Hours slept last night", 0, 12, 8)

st.markdown("---")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Start reaction test", use_container_width=True):
        st.session_state.reaction_state = "waiting"
        st.session_state.ready_time = time.time() + random.uniform(2, 5)
        st.session_state.start_time = None

with col2:
    if st.button("Reset", use_container_width=True):
        st.session_state.reaction_state = "idle"
        st.session_state.ready_time = None
        st.session_state.start_time = None

if st.session_state.reaction_state == "waiting":
    if time.time() >= st.session_state.ready_time:
        st.session_state.reaction_state = "ready"
        st.session_state.start_time = time.time()
    else:
        st.info("Waiting for green...")

if st.session_state.reaction_state == "ready":
    st.success("TAP NOW!")
    if st.button("Tap!", key="tap_button", use_container_width=True):
        ms = int((time.time() - st.session_state.start_time) * 1000)
        result = {
            "time": datetime.now().strftime("%m/%d %I:%M %p"),
            "sleep_hours": sleep,
            "reaction_ms": ms,
        }
        st.session_state.result_history.append(result)

        history_df = pd.DataFrame(st.session_state.result_history)
        history_df.to_csv(CSV_PATH, index=False)

        readiness_score, readiness_label = calculate_readiness_score(sleep, ms)

        st.session_state.last_reaction_ms = ms
        st.session_state.last_readiness_score = readiness_score
        st.session_state.last_readiness_label = readiness_label
        st.session_state.reaction_state = "complete"

if st.session_state.reaction_state == "idle":
    st.info("Press Start reaction test when you're ready.")

if st.session_state.reaction_state == "complete":
    latest = st.session_state.result_history[-1]
    score, label = calculate_readiness_score(latest["sleep_hours"], latest["reaction_ms"])

    st.markdown("---")
    st.subheader("Readiness dashboard")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Sleep", f"{latest['sleep_hours']}h")
    with col_b:
        st.metric("Last reaction", f"{latest['reaction_ms']} ms")
    with col_c:
        st.metric("Readiness score", f"{score}/100")
    with col_d:
        st.metric("Status", label)

    if st.session_state.result_history:
        history_df = pd.DataFrame(st.session_state.result_history)
        history_df["reaction_ms"] = history_df["reaction_ms"].astype(int)
        history_df["sleep_hours"] = history_df["sleep_hours"].astype(float)

        avg_reaction = round(history_df["reaction_ms"].mean())
        avg_sleep = round(history_df["sleep_hours"].mean(), 1)

        st.write(f"Average reaction: {avg_reaction} ms")
        st.write(f"Average sleep: {avg_sleep} hours")

        st.line_chart(history_df.set_index("time")["reaction_ms"])

        st.subheader("Recent results")
        st.dataframe(history_df, use_container_width=True)
    else:
        st.write("No results yet.")

if st.session_state.result_history and st.session_state.reaction_state not in ["complete", "ready"]:
    history_df = pd.DataFrame(st.session_state.result_history)
    if not history_df.empty:
        st.markdown("---")
        st.subheader("Recent results")
        st.dataframe(history_df.tail(5), use_container_width=True)
