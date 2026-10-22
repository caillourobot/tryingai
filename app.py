import streamlit as st
import time, random
from datetime import datetime

st.set_page_config(page_title="AviaWake", page_icon=":airplane:"
st.markdown("<style>@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap'); h1{font-family:'Playfair Display', serif !important; font-weight:700;}</style>", unsafe_allow_html=True)

st.title("AviaWake")
st.write("Pilot Fatigue & Readiness Tracker")
sleep = st.slider("Hours slept last night", 0, 12, 8)
st.write("---"

if st.button("START REACTION TEST", use_container_width=True):
         with st.spinner("Wait for GREEN..."):
            time.sleep(random.uniform(2,4))
         start = time.time()
         st.success("TAP NOW!")
         if st.button("TAP!"):
              ms = int((time.time()-start*1000)
              st.metric("Reaction", f"{ms} ms")
              st.write(f"Saved: {datetime.now().strftime('%m/%d %I:%M %p')} | {sleep}h sleep")
