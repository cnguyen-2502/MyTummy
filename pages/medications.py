import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from datetime import date, datetime

FREQUENCIES = ["Once daily", "Twice daily", "Three times daily", "Weekly", "As needed", "Other"]

def render(dm):
    st.markdown('<div class="page-header">Medications & Visits</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Track your medications, supplements, and doctor appointments</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Medications & Supplements", "Appointments"])

    # -- Medications --
    with tab1:
        st.markdown('<div class="card-title" style="margin-top:1rem">Add Medication / Supplement</div>',
                    unsafe_allow_html=True)

        with st.form("add_med"):
            c1, c2 = st.columns(2)
            with c1:
                med_name = st.text_input("Medication name", placeholder="e.g. Prenatal vitamins, Iron tablets")
            with c2:
                med_dose = st.text_input("Dose", placeholder="e.g. 400mg, 1 tablet")
            c1, c2 = st.columns(2)
            with c1:
                med_freq = st.selectbox("Frequency", FREQUENCIES)
            with c2:
                med_start = st.date_input("Start date", value=date.today())
            med_notes = st.text_input("Notes (optional)", placeholder="e.g. Take with food")
            submitted = st.form_submit_button("Add Medication", use_container_width=True)
            if submitted and med_name:
                dm.add_medication({
                    "name": med_name,
                    "dose": med_dose,
                    "frequency": med_freq,
                    "start_date": str(med_start),
                    "notes": med_notes,
                })
                st.success(f"{med_name} added!")
                st.rerun()

        # Current medications list
        meds = dm.get_medications()
        if meds:
            st.markdown("---")
            st.markdown('<div class="card-title">Current Medications</div>', unsafe_allow_html=True)
            for med in meds:
                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        st.markdown(f"**{med['name']}** — {med.get('dose', '')}")
                        st.caption(f"{med.get('frequency', '')} · Started {med.get('start_date', '')}")
                        if med.get("notes"):
                            st.caption(f"{med['notes']}")
                    with c2:
                        st.markdown(f"<div class='stat-pill' style='margin-top:0.5rem'>{med.get('frequency','')}</div>",
                                    unsafe_allow_html=True)
                    with c3:
                        if st.button("Delete", key=f"del_med_{med['id']}"):
                            dm.delete_medication(med["id"])
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("No medications logged yet. Add your prenatal vitamins and supplements!")

    # -- Appointments --
    with tab2:
        st.markdown('<div class="card-title" style="margin-top:1rem">Log an Appointment</div>',
                    unsafe_allow_html=True)

        with st.form("add_appt"):
            c1, c2 = st.columns(2)
            with c1:
                appt_type = st.selectbox("Appointment type", [
                    "OB/GYN visit", "Ultrasound", "Blood test", "Anatomy scan",
                    "Non-stress test (NST)", "Glucose screening", "Dental", "Mental health", "Other"
                ])
            with c2:
                appt_date = st.date_input("Date", value=date.today())
            c1, c2 = st.columns(2)
            with c1:
                appt_provider = st.text_input("Provider name", placeholder="Dr. Smith")
            with c2:
                appt_location = st.text_input("Location / clinic", placeholder="City OB Clinic")
            appt_notes = st.text_area("Notes / findings", height=80,
                                      placeholder="What was discussed? Any test results or next steps?")
            submitted = st.form_submit_button("Save Appointment", use_container_width=True)
            if submitted:
                dm.add_appointment({
                    "type": appt_type,
                    "date": str(appt_date),
                    "provider": appt_provider,
                    "location": appt_location,
                    "notes": appt_notes,
                })
                st.success("Appointment saved!")
                st.rerun()

        # Appointments list
        appts = sorted(dm.get_appointments(), key=lambda x: x.get("date", ""), reverse=True)
        if appts:
            st.markdown("---")
            upcoming = [a for a in appts if a.get("date", "") >= str(date.today())]
            past = [a for a in appts if a.get("date", "") < str(date.today())]

            if upcoming:
                st.markdown('<div class="card-title">Upcoming</div>', unsafe_allow_html=True)
                for appt in sorted(upcoming, key=lambda x: x.get("date","")):
                    _render_appt(appt, dm)

            if past:
                st.markdown('<div class="card-title">Past Appointments</div>', unsafe_allow_html=True)
                for appt in past:
                    _render_appt(appt, dm)
        else:
            st.info("No appointments logged yet.")

def _render_appt(appt, dm):
    with st.container():
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"**{appt.get('type','Appointment')}** · {appt.get('date','')}")
            if appt.get("provider"):
                st.caption(f"{appt['provider']} · {appt.get('location','')}")
            if appt.get("notes"):
                st.caption(f"{appt['notes']}")
        with c2:
            if st.button("Delete", key=f"del_appt_{appt['id']}"):
                dm.delete_appointment(appt["id"])
                st.rerun()
        st.markdown("---")