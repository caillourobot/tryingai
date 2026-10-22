import streamlit as st
import time, random
from datetime import datetime

st.set_page_config(page_title="AviaWake", page_icon=":airplane:")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
    h1 {
        font-family:'Playfair Display', serif !important;
        font-weight:700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AviaWake")
st.write("Pilot Fatigue & Readiness Tracker")
sleep = st.slider("Hours slept last night", 0, 12, 8)
st.write("---")

if "reaction_state" not in st.session_state:
    st.session_state.reaction_state = "idle"
if "target_time" not in st.session_state:
    st.session_state.target_time = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None

if st.button("START REACTION TEST", use_container_width=True):
    st.session_state.target_time = time.time() + random.uniform(2, 4)
    st.session_state.reaction_state = "waiting"
    st.session_state.start_time = None

if st.session_state.reaction_state == "waiting":
    if time.time() >= st.session_state.target_time:
        st.session_state.reaction_state = "ready"
        st.session_state.start_time = time.time()
    else:
        st.info("Wait for GREEN...")

if st.session_state.reaction_state == "ready":
    st.success("TAP NOW!")
    if st.button("TAP!", key="tap_button", use_container_width=True):
        ms = int((time.time() - st.session_state.start_time) * 1000)
        st.metric("Reaction", f"{ms} ms")
        st.write(f"Saved: {datetime.now().strftime('%m/%d %I:%M %p')} | {sleep}h sleep")
        st.session_state.reaction_state = "idle"
        st.session_state.start_time = None
        st.session_state.target_time = None
