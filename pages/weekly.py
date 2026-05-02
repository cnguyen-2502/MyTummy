import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from utils.helpers import get_week_of_pregnancy, get_trimester

WEIGHT_GAIN_RANGES = {
    "Underweight (BMI < 18.5)": (28, 40),
    "Normal weight (BMI 18.5–24.9)": (25, 35),
    "Overweight (BMI 25–29.9)": (15, 25),
    "Obese (BMI 30+)": (11, 20),
}

def render(dm):
    st.markdown('<div class="page-header">Weekly Check-in</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Body metrics, fetal health, and weekly summary</div>', unsafe_allow_html=True)

    due_date = st.session_state.get("due_date")
    if not due_date:
        st.info("Set your due date first.")
        return

    week, _ = get_week_of_pregnancy(due_date)
    trimester = get_trimester(week)

    existing_weekly = {}
    for log in dm.get_weekly_logs():
        if log.get("week") == week:
            existing_weekly = log
            break

    if existing_weekly:
        st.markdown(f'<div class="card" style="border-color:var(--rose)">Week {week} check-in saved. You can update below.</div>',
                    unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Body Metrics", "Fetal Health", "Environmental"])

    with tab1:
        st.markdown('<div class="card-title" style="margin-top:1rem">Weight</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            weight = st.number_input("Current weight (lbs)", 80.0, 350.0,
                                     float(existing_weekly.get("weight", 140.0)), 0.5)
        with c2:
            if "pre_weight" not in st.session_state:
                st.session_state.pre_weight = dm.get_setting("pre_weight") or 130.0
            pre_weight = st.number_input("Pre-pregnancy weight (lbs)", 80.0, 350.0,
                                         float(st.session_state.pre_weight), 0.5)
            if st.button("Save pre-pregnancy weight"):
                dm.save_setting("pre_weight", str(pre_weight))
                st.session_state.pre_weight = pre_weight

        gained = weight - float(dm.get_setting("pre_weight") or pre_weight)
        bmi_cat = st.selectbox("Pre-pregnancy BMI category", list(WEIGHT_GAIN_RANGES.keys()), index=1)
        low, high = WEIGHT_GAIN_RANGES[bmi_cat]

        if low <= gained <= high:
            range_status = "Within recommended range"
        elif gained > high:
            range_status = "Above recommended range"
        else:
            range_status = "Below recommended range"

        st.markdown(f"""
        <div class="card">
            <div class="card-title">Weight Gain Analysis</div>
            <div style="display:flex;gap:2rem;align-items:center">
                <div>
                    <div class="metric-val">{gained:+.1f} lbs</div>
                    <div class="metric-lbl">Total gain</div>
                </div>
                <div style="font-size:0.85rem;color:var(--text-muted)">
                    Recommended range: <b>{low}–{high} lbs</b> total<br>
                    {range_status}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="card-title">Blood Pressure</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            bp_sys = st.number_input("Systolic (top number)", 70, 200,
                                     int(existing_weekly.get("bp_sys", 115)))
        with c2:
            bp_dia = st.number_input("Diastolic (bottom number)", 40, 130,
                                     int(existing_weekly.get("bp_dia", 75)))

        if bp_sys >= 140 or bp_dia >= 90:
            st.markdown('<div class="alert-card">High blood pressure detected (140/90 or above). This may indicate preeclampsia. Contact your doctor immediately.</div>',
                        unsafe_allow_html=True)
        elif bp_sys >= 130 or bp_dia >= 80:
            st.markdown('<div class="warning-card">Elevated blood pressure. Monitor closely and inform your provider.</div>',
                        unsafe_allow_html=True)
        elif bp_sys < 90 or bp_dia < 60:
            st.markdown('<div class="alert-card">Low blood pressure detected (below 90/60). Hypotension during pregnancy can reduce blood flow to the baby. Contact your doctor if you experience dizziness, fainting, or nausea.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card">Blood pressure {bp_sys}/{bp_dia} mmHg — within normal range.</div>',
                        unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="card-title">Blood Sugar (if monitoring)</div>', unsafe_allow_html=True)
        track_sugar = st.checkbox("Track blood sugar this week", value=existing_weekly.get("track_sugar", False))
        blood_sugar = None
        if track_sugar:
            c1, c2 = st.columns(2)
            with c1:
                sugar_fasting = st.number_input("Fasting blood glucose (mg/dL)", 50, 300,
                                                 int(existing_weekly.get("sugar_fasting", 90)))
            with c2:
                sugar_postmeal = st.number_input("Post-meal glucose (mg/dL, 1hr after)", 50, 400,
                                                  int(existing_weekly.get("sugar_postmeal", 130)))
            if sugar_fasting > 95:
                st.markdown('<div class="warning-card">Fasting glucose above 95 mg/dL. Discuss with your doctor.</div>',
                            unsafe_allow_html=True)
            if sugar_postmeal > 140:
                st.markdown('<div class="warning-card">Post-meal glucose above 140 mg/dL. Monitor diet and consult your provider.</div>',
                            unsafe_allow_html=True)
            blood_sugar = {"fasting": sugar_fasting, "postmeal": sugar_postmeal}

    with tab2:
        st.markdown('<div class="card-title" style="margin-top:1rem">Fetal Movement</div>', unsafe_allow_html=True)

        if week >= 20:
            st.caption("Count fetal movements — kicks, rolls, jabs. Aim for 10 in 2 hours.")
            kick_count = st.number_input("Kick count in 2 hours", 0, 50,
                                         int(existing_weekly.get("kick_count", 0)))
            kick_time_min = st.number_input("Time to reach 10 kicks (minutes, 0 if not yet reached)", 0, 120,
                                            int(existing_weekly.get("kick_time", 0)))
            if kick_count < 10 and week >= 28:
                st.markdown('<div class="warning-card">Fewer than 10 movements in 2 hours after week 28. Contact your provider if this continues.</div>',
                            unsafe_allow_html=True)
        else:
            st.info(f"Fetal movement tracking typically begins around week 20. You are currently at week {week}.")
            kick_count = 0
            kick_time_min = 0

        st.markdown("---")
        if week >= 28:
            st.markdown('<div class="card-title">Contractions (if occurring)</div>', unsafe_allow_html=True)
            contractions = st.checkbox("Track contractions this week", value=existing_weekly.get("contractions", False))
            contraction_freq = 0
            contraction_duration = 0
            if contractions:
                c1, c2 = st.columns(2)
                with c1:
                    contraction_freq = st.number_input("Frequency (minutes apart)", 1, 60,
                                                       int(existing_weekly.get("contraction_freq", 10)))
                with c2:
                    contraction_duration = st.number_input("Duration (seconds)", 10, 120,
                                                           int(existing_weekly.get("contraction_duration", 30)))
                if week < 37 and contraction_freq <= 10:
                    st.markdown('<div class="alert-card">Frequent contractions before 37 weeks may indicate preterm labour. Contact your doctor immediately.</div>',
                                unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card-title" style="margin-top:1rem">Environmental Factors</div>', unsafe_allow_html=True)
        travel = st.checkbox("Travelled this week", value=existing_weekly.get("travel", False))
        travel_notes = ""
        if travel:
            travel_notes = st.text_input("Where / how long?", value=existing_weekly.get("travel_notes", ""))

        illness_exposure = st.checkbox("Possible illness exposure", value=existing_weekly.get("illness_exposure", False))
        illness_notes = ""
        if illness_exposure:
            illness_notes = st.text_input("Details (optional)", value=existing_weekly.get("illness_notes", ""))
            st.info("Inform your provider of any illness exposures, especially fever or respiratory illness.")

        stress_events = st.text_area("Major stress or life events this week?",
                                     value=existing_weekly.get("stress_events", ""),
                                     height=80)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Week Check-in", use_container_width=True):
        log = {
            "week": week,
            "trimester": trimester,
            "weight": weight,
            "bp_sys": bp_sys,
            "bp_dia": bp_dia,
            "track_sugar": track_sugar,
            "kick_count": kick_count,
            "kick_time": kick_time_min,
            "travel": travel,
            "travel_notes": travel_notes,
            "illness_exposure": illness_exposure,
            "illness_notes": illness_notes,
            "stress_events": stress_events,
        }
        if track_sugar and blood_sugar:
            log["sugar_fasting"] = blood_sugar["fasting"]
            log["sugar_postmeal"] = blood_sugar["postmeal"]
        if week >= 28 and "contractions" in locals():
            log["contractions"] = contractions
            if contractions:
                log["contraction_freq"] = contraction_freq
                log["contraction_duration"] = contraction_duration
        dm.save_weekly_log(log)
        st.success(f"Week {week} check-in saved.")