import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st
from datetime import date, datetime

from utils.data_manager import DataManager
from utils.helpers import get_trimester, get_week_of_pregnancy

st.set_page_config(
    page_title="MyTummy 🌸",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

css_path = os.path.join(APP_DIR, "utils", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
/* Fix clipped multiselect tag */
[data-baseweb="select"] span[data-baseweb="tag"]:first-of-type {
    margin-left: 20px !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
@keyframes flash-success {
    0%   { box-shadow: 0 0 0 0 rgba(224, 115, 125, 0.6); }
    50%  { box-shadow: 0 0 0 12px rgba(224, 115, 125, 0.15); }
    100% { box-shadow: 0 0 0 0 rgba(224, 115, 125, 0); }
}
[data-testid="stSuccess"] {
    animation: flash-success 0.8s ease-out forwards;
}
</style>
""", unsafe_allow_html=True)

dm = DataManager()

if "due_date" not in st.session_state:
    stored = dm.get_setting("due_date")
    st.session_state.due_date = stored if stored else None
if "name" not in st.session_state:
    stored = dm.get_setting("name")
    st.session_state.name = stored if stored else "Mama"

PAGES = {
    "Home": "Home",
    "Daily Log": "Daily Log",
    "Weekly": "Weekly Check-in",
    "Meds": "Medications & Visits",
    "Journal": "Journal",
    "Analytics": "Analytics",
    "Guidance": "Guidance",
}

# ── Top bar ───────────────────────────────────────
st.markdown('<div class="top-bar"><span class="top-logo">🌸 MyTummy</span></div>',
            unsafe_allow_html=True)

if st.session_state.due_date:
    week, _ = get_week_of_pregnancy(st.session_state.due_date)
    trimester = get_trimester(week)
    st.markdown(f"""
    <div class="preg-stats" style="margin-bottom:0.5rem">
        <div class="stat-pill">Week {week}</div>
        <div class="stat-pill">{trimester}</div>
        <div class="stat-pill">{st.session_state.name}</div>
    </div>
    """, unsafe_allow_html=True)

if "nav_target" in st.session_state:
    st.session_state["main_nav"] = st.session_state.pop("nav_target")

page = st.selectbox("", list(PAGES.keys()), label_visibility="collapsed", key="main_nav")
st.markdown("---")

page_key = PAGES[page]

if not st.session_state.due_date and page_key == "Home":
    st.markdown('<div class="card-title">⚙️ Let\'s get you set up</div>', unsafe_allow_html=True)
    name_input = st.text_input("Your name", value=st.session_state.name)
    due = st.date_input("Due date", value=date(2025, 6, 15))
    if st.button("Save Setup", use_container_width=True):
        st.session_state.due_date = str(due)
        st.session_state.name = name_input
        dm.save_setting("due_date", str(due))
        dm.save_setting("name", name_input)
        st.success("Saved!")
        st.rerun()

with st.expander("Update pregnancy details"):
    name_input = st.text_input("Your name", value=st.session_state.name, key="name_top")
    due = st.date_input(
        "Due date",
        value=date(2025, 6, 15) if not st.session_state.due_date
        else datetime.strptime(st.session_state.due_date, "%Y-%m-%d").date(),
        key="due_top"
    )
    if st.button("Save", use_container_width=True, key="save_top"):
        st.session_state.due_date = str(due)
        st.session_state.name = name_input
        dm.save_setting("due_date", str(due))
        dm.save_setting("name", name_input)
        st.success("Saved!")
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if page_key == "Home":
    from pages.home import render
elif page_key == "Daily Log":
    from pages.daily_log import render
elif page_key == "Weekly Check-in":
    from pages.weekly import render
elif page_key == "Medications & Visits":
    from pages.medications import render
elif page_key == "Journal":
    from pages.calendar_view import render
elif page_key == "Analytics":
    from pages.analytics import render
elif page_key == "Guidance":
    from pages.guidance import render

render(dm)