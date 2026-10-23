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
ORIENTATION_CSV_PATH = "orientation_history.csv"
MEMORY_CSV_PATH = "memory_history.csv"


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


def get_strength_label(score):
    if score >= 80:
        return "Ready"
    elif score >= 65:
        return "Monitor"
    else:
        return "Not recommended for duty"


def get_readiness_message(score):
    if score >= 80:
        return "Strong readiness. Cognitive speed and sleep are in a healthy range."
    elif score >= 65:
        return "Moderate readiness. Consider monitoring workload and fatigue closely."
    else:
        return "Low readiness. Consider delaying demanding tasks or reducing workload."


if "pilot_name" not in st.session_state:
    st.session_state.pilot_name = "Pilot 1"
if "notes" not in st.session_state:
    st.session_state.notes = ""
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

if "orientation_state" not in st.session_state:
    st.session_state.orientation_state = "idle"
if "orientation_target" not in st.session_state:
    st.session_state.orientation_target = 0
if "orientation_start" not in st.session_state:
    st.session_state.orientation_start = None
if "orientation_answer" not in st.session_state:
    st.session_state.orientation_answer = "left"
if "orientation_history" not in st.session_state:
    if os.path.exists(ORIENTATION_CSV_PATH):
        try:
            saved_df = pd.read_csv(ORIENTATION_CSV_PATH)
            if not saved_df.empty:
                st.session_state.orientation_history = saved_df.to_dict("records")
            else:
                st.session_state.orientation_history = []
        except Exception:
            st.session_state.orientation_history = []
    else:
        st.session_state.orientation_history = []

if "memory_state" not in st.session_state:
    st.session_state.memory_state = "idle"
if "memory_sequence" not in st.session_state:
    st.session_state.memory_sequence = []
if "memory_guess" not in st.session_state:
    st.session_state.memory_guess = []
if "memory_started_at" not in st.session_state:
    st.session_state.memory_started_at = None
if "memory_result" not in st.session_state:
    st.session_state.memory_result = None
if "memory_history" not in st.session_state:
    if os.path.exists(MEMORY_CSV_PATH):
        try:
            saved_df = pd.read_csv(MEMORY_CSV_PATH)
            if not saved_df.empty:
                st.session_state.memory_history = saved_df.to_dict("records")
            else:
                st.session_state.memory_history = []
        except Exception:
            st.session_state.memory_history = []
    else:
        st.session_state.memory_history = []

st.session_state.pilot_name = st.text_input("Pilot name", value=st.session_state.pilot_name)
st.session_state.notes = st.text_area("Notes", value=st.session_state.notes, placeholder="Late night, missed meal, stress, etc.")

sleep = st.slider("Hours slept last night", 0, 12, 8)
mission_phase = st.selectbox("Mission phase", ["Cruise", "Approach", "Taxi", "High workload"])

st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])
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
with col3:
    if st.button("Clear history", use_container_width=True):
        st.session_state.result_history = []
        st.session_state.orientation_history = []
        st.session_state.memory_history = []
        for path in [CSV_PATH, ORIENTATION_CSV_PATH, MEMORY_CSV_PATH]:
            if os.path.exists(path):
                os.remove(path)

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
            "pilot_name": st.session_state.pilot_name,
            "time": datetime.now().strftime("%m/%d %I:%M %p"),
            "sleep_hours": sleep,
            "reaction_ms": ms,
            "mission_phase": mission_phase,
            "notes": st.session_state.notes,
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

    strength = get_strength_label(score)
    message = get_readiness_message(score)

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Sleep", f"{latest['sleep_hours']}h")
    with col_b:
        st.metric("Last reaction", f"{latest['reaction_ms']} ms")
    with col_c:
        st.metric("Readiness score", f"{score}/100")
    with col_d:
        st.metric("Status", strength)

    st.success(message)

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
        st.dataframe(history_df.tail(5), use_container_width=True)

        if st.button("Download reaction log", use_container_width=True):
            csv = history_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="reaction_history.csv",
                mime="text/csv",
            )

    else:
        st.write("No results yet.")

if st.session_state.result_history and st.session_state.reaction_state not in ["complete", "ready"]:
    history_df = pd.DataFrame(st.session_state.result_history)
    if not history_df.empty:
        st.markdown("---")
        st.subheader("Recent results")
        st.dataframe(history_df.tail(5), use_container_width=True)

st.markdown("---")
st.subheader("Orientation challenge")

if st.button("Start orientation drill", key="orientation_start", use_container_width=True):
    st.session_state.orientation_state = "ready"
    tilt_options = [-60, -45, -30, 30, 45, 60]
    st.session_state.orientation_target = random.choice(tilt_options)
    st.session_state.orientation_start = time.time()
    st.session_state.orientation_answer = "left" if st.session_state.orientation_target < 0 else "right"

if st.session_state.orientation_state == "ready":
    tilt = st.session_state.orientation_target
    st.markdown(
        f"<div style='text-align:center; font-size:120px; transform: rotate({tilt}deg);'>✈️</div>",
        unsafe_allow_html=True,
    )
    st.write(f"Correct the aircraft to level: choose {st.session_state.orientation_answer.upper()}.")

    col_left, col_right = st.columns(2)
    with col_left:
        if st.button("LEFT", key="ori_left", use_container_width=True):
            elapsed_ms = int((time.time() - st.session_state.orientation_start) * 1000)
            accuracy = 1 if st.session_state.orientation_answer == "left" else 0
            result = {
                "pilot_name": st.session_state.pilot_name,
                "time": datetime.now().strftime("%m/%d %I:%M %p"),
                "response_ms": elapsed_ms,
                "accuracy": accuracy,
                "expected_direction": st.session_state.orientation_answer,
                "selected_direction": "left",
                "mission_phase": mission_phase,
                "notes": st.session_state.notes,
            }
            st.session_state.orientation_history.append(result)
            pd.DataFrame(st.session_state.orientation_history).to_csv(ORIENTATION_CSV_PATH, index=False)
            st.session_state.orientation_state = "result"
            st.session_state.orientation_last_ms = elapsed_ms
            st.session_state.orientation_last_accuracy = accuracy

    with col_right:
        if st.button("RIGHT", key="ori_right", use_container_width=True):
            elapsed_ms = int((time.time() - st.session_state.orientation_start) * 1000)
            accuracy = 1 if st.session_state.orientation_answer == "right" else 0
            result = {
                "pilot_name": st.session_state.pilot_name,
                "time": datetime.now().strftime("%m/%d %I:%M %p"),
                "response_ms": elapsed_ms,
                "accuracy": accuracy,
                "expected_direction": st.session_state.orientation_answer,
                "selected_direction": "right",
                "mission_phase": mission_phase,
                "notes": st.session_state.notes,
            }
            st.session_state.orientation_history.append(result)
            pd.DataFrame(st.session_state.orientation_history).to_csv(ORIENTATION_CSV_PATH, index=False)
            st.session_state.orientation_state = "result"
            st.session_state.orientation_last_ms = elapsed_ms
            st.session_state.orientation_last_accuracy = accuracy

if st.session_state.orientation_state == "result":
    speed = st.session_state.orientation_last_ms
    accuracy = st.session_state.orientation_last_accuracy
    accuracy_pct = 100 if accuracy == 1 else 0

    st.metric("Orientation speed", f"{speed} ms")
    st.metric("Accuracy", f"{accuracy_pct}%")

    if accuracy == 1:
        st.success("Correct response. Good spatial orientation.")
    else:
        st.warning("Incorrect response. Consider more cautious workload management.")

    if st.button("Try another orientation", key="orientation_retry", use_container_width=True):
        st.session_state.orientation_state = "ready"
        tilt_options = [-60, -45, -30, 30, 45, 60]
        st.session_state.orientation_target = random.choice(tilt_options)
        st.session_state.orientation_start = time.time()
        st.session_state.orientation_answer = "left" if st.session_state.orientation_target < 0 else "right"

    if st.session_state.orientation_history:
        hist = pd.DataFrame(st.session_state.orientation_history)
        avg_speed = round(hist["response_ms"].mean())
        avg_accuracy = round(hist["accuracy"].mean() * 100)
        st.write(f"Average speed: {avg_speed} ms")
        st.write(f"Average accuracy: {avg_accuracy}%")
        st.dataframe(hist.tail(5), use_container_width=True)

        if st.button("Download orientation log", use_container_width=True):
            csv = hist.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="orientation_history.csv",
                mime="text/csv",
            )

if st.session_state.orientation_history and st.session_state.orientation_state == "idle":
    hist = pd.DataFrame(st.session_state.orientation_history)
    if not hist.empty:
        st.write("Latest orientation results:")
        st.dataframe(hist.tail(5), use_container_width=True)

st.markdown("---")
st.subheader("Memory challenge")

memory_icons = ["✈️", "🧭", "⏱️", "📡", "🌙", "⚙️", "🛰️", "🛬", "🛫", "⚡"]

if st.button("Start memory challenge", key="memory_start", use_container_width=True):
    st.session_state.memory_sequence = random.sample(memory_icons, random.randint(3, 5))
    st.session_state.memory_guess = []
    st.session_state.memory_started_at = time.time()
    st.session_state.memory_state = "showing"
    st.session_state.memory_result = None

if st.session_state.memory_state == "showing":
    st.write("Memorize the pattern:")
    display = " ".join(st.session_state.memory_sequence)
    st.markdown(f"<div style='font-size:60px; text-align:center'>{display}</div>", unsafe_allow_html=True)
    if time.time() - st.session_state.memory_started_at >= 3:
        st.session_state.memory_state = "guessing"
        st.session_state.memory_started_at = None

if st.session_state.memory_state == "guessing":
    st.write("Repeat the pattern in order:")
    cols = st.columns(5)
    for idx, icon in enumerate(memory_icons):
        with cols[idx % 5]:
            if st.button(icon, key=f"memory_icon_{idx}", use_container_width=True):
                st.session_state.memory_guess.append(icon)
                expected = st.session_state.memory_sequence[len(st.session_state.memory_guess) - 1]
                if icon != expected:
                    st.session_state.memory_result = {
                        "passed": False,
                        "message": "Incorrect sequence. Try again.",
                        "guess": st.session_state.memory_guess.copy(),
                    }
                    st.session_state.memory_state = "result"
                    memory_record = {
                        "pilot_name": st.session_state.pilot_name,
                        "time": datetime.now().strftime("%m/%d %I:%M %p"),
                        "score": 0,
                        "correct": 0,
                        "sequence": "".join(st.session_state.memory_sequence),
                        "guess": "".join(st.session_state.memory_guess),
                        "mission_phase": mission_phase,
                        "notes": st.session_state.notes,
                    }
                    st.session_state.memory_history.append(memory_record)
                    pd.DataFrame(st.session_state.memory_history).to_csv(MEMORY_CSV_PATH, index=False)
                elif len(st.session_state.memory_guess) == len(st.session_state.memory_sequence):
                    st.session_state.memory_result = {
                        "passed": True,
                        "message": "Perfect memory. Sequence matched.",
                        "guess": st.session_state.memory_guess.copy(),
                    }
                    st.session_state.memory_state = "result"
                    memory_record = {
                        "pilot_name": st.session_state.pilot_name,
                        "time": datetime.now().strftime("%m/%d %I:%M %p"),
                        "score": 100,
                        "correct": len(st.session_state.memory_sequence),
                        "sequence": "".join(st.session_state.memory_sequence),
                        "guess": "".join(st.session_state.memory_guess),
                        "mission_phase": mission_phase,
                        "notes": st.session_state.notes,
                    }
                    st.session_state.memory_history.append(memory_record)
                    pd.DataFrame(st.session_state.memory_history).to_csv(MEMORY_CSV_PATH, index=False)

    if st.session_state.memory_guess:
        st.write("Your current guess: " + " ".join(st.session_state.memory_guess))

if st.session_state.memory_state == "result":
    if st.session_state.memory_result:
        if st.session_state.memory_result["passed"]:
            st.success(st.session_state.memory_result["message"])
            st.metric("Memory score", "100%")
        else:
            st.warning(st.session_state.memory_result["message"])
            st.metric("Memory score", "0%")

    if st.button("Try another memory challenge", key="memory_retry", use_container_width=True):
        st.session_state.memory_sequence = random.sample(memory_icons, random.randint(3, 5))
        st.session_state.memory_guess = []
        st.session_state.memory_state = "showing"
        st.session_state.memory_started_at = time.time()
        st.session_state.memory_result = None

    if st.session_state.memory_history:
        hist = pd.DataFrame(st.session_state.memory_history)
        st.subheader("Latest memory results")
        st.dataframe(hist.tail(5), use_container_width=True)

        if st.button("Download memory log", use_container_width=True):
            csv = hist.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="memory_history.csv",
                mime="text/csv",
            )

if st.session_state.memory_history and st.session_state.memory_state == "idle":
    hist = pd.DataFrame(st.session_state.memory_history)
    if not hist.empty:
        st.write("Latest memory results:")
        st.dataframe(hist.tail(5), use_container_width=True)

st.markdown("---")
st.subheader("Weekly readiness summary")

all_results = []
if st.session_state.result_history:
    all_results.extend(st.session_state.result_history)
if st.session_state.orientation_history:
    all_results.extend(st.session_state.orientation_history)
if st.session_state.memory_history:
    all_results.extend(st.session_state.memory_history)

if all_results:
    summary_df = pd.DataFrame(all_results)
    if "reaction_ms" in summary_df.columns:
        summary_df["reaction_ms"] = pd.to_numeric(summary_df["reaction_ms"], errors="coerce")
        summary_df["sleep_hours"] = pd.to_numeric(summary_df.get("sleep_hours", 0), errors="coerce")
        if not summary_df.empty:
            avg_reaction = round(summary_df["reaction_ms"].mean())
            avg_sleep = round(summary_df["sleep_hours"].mean(), 1)
            st.write(f"Average reaction: {avg_reaction} ms")
            st.write(f"Average sleep: {avg_sleep} hours")

    if "accuracy" in summary_df.columns:
        summary_df["accuracy"] = pd.to_numeric(summary_df["accuracy"], errors="coerce")
        avg_accuracy = round(summary_df["accuracy"].mean() * 100)
        st.write(f"Average orientation accuracy: {avg_accuracy}%")

    if "score" in summary_df.columns:
        avg_memory = round(summary_df["score"].mean())
        st.write(f"Average memory score: {avg_memory}%")
else:
    st.write("No data yet. Start a test to begin tracking readiness.")
