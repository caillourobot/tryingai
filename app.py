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
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AviaWake")
st.caption("Pilot Fatigue & Readiness Tracker")

if "reaction_state" not in st.session_state:
    st.session_state.reaction_state = "idle"
if "ready_time" not in st.session_state:
    st.session_state.ready_time = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "result_history" not in st.session_state:
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

        csv_path = "reaction_history.csv"
        history_df = pd.DataFrame(st.session_state.result_history)
        history_df.to_csv(csv_path, index=False)

        st.metric("Reaction time", f"{ms} ms")
        st.write(f"Saved: {result['time']} | {sleep}h sleep")
        st.success("Test complete.")
        st.session_state.reaction_state = "complete"

if st.session_state.reaction_state == "complete":
    st.markdown("---")
    st.subheader("Recent results")
    if st.session_state.result_history:
        history_df = pd.DataFrame(st.session_state.result_history)
        st.dataframe(history_df, use_container_width=True)
    else:
        st.write("No results yet.")

if st.session_state.reaction_state == "idle":
    st.info("Press Start reaction test when you're ready.")
