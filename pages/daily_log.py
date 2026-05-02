import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from datetime import date
from utils.helpers import compute_daily_score, score_color, score_label

SYMPTOMS = [
    "nausea", "vomiting", "headache", "swelling", "bleeding",
    "cramps", "heartburn", "back pain", "fatigue", "shortness of breath"
]

MOOD_LABELS      = {1: "Very stressed", 2: "Stressed", 3: "Neutral", 4: "Calm", 5: "Very calm"}
SLEEP_LABELS     = {1: "Awful", 2: "Poor", 3: "Okay", 4: "Good", 5: "Great"}
ENERGY_LABELS    = {1: "Exhausted", 2: "Very tired", 3: "Okay", 4: "Good", 5: "Great"}
HYDRATION_LABELS = ["Poor", "Okay", "Good"]

PRENATAL_VITAMINS = [
    ("folic_acid",  "Folic acid (400–800 mcg)"),
    ("iron",        "Iron (27 mg)"),
    ("calcium_vit_d", "Calcium & Vitamin D"),
    ("iodine",      "Iodine"),
    ("dha_omega3",  "DHA / Omega-3"),
]


def render(dm):
    st.markdown('<div class="page-header">Daily Log</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">How are you feeling today?</div>', unsafe_allow_html=True)

    today = str(date.today())
    existing = dm.get_daily_log_for(today) or {}

    if existing:
        score = compute_daily_score(existing)
        color = score_color(score)
        label = score_label(score)
        st.markdown(f"""
        <div class="card" style="border-color:var(--rose)">
            <div class="card-title">Today's log saved</div>
            <div style="display:flex;align-items:center;gap:1.25rem">
                <div class="score-circle" style="background:linear-gradient(135deg,{color},{color}bb)">
                    <div class="score-num">{score}</div>
                    <div class="score-label">{label}</div>
                </div>
                <div style="font-size:0.88rem;color:var(--text-light)">You can update your log below anytime.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Mood ──────────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Mood</div>', unsafe_allow_html=True)
    mood = st.slider("How are you feeling emotionally?", 1, 5, existing.get("mood", 3))
    st.caption(MOOD_LABELS.get(mood, ""))

    st.markdown("---")

    # ── Energy ────────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Energy</div>', unsafe_allow_html=True)
    energy = st.slider("What is your energy level today?", 1, 5, existing.get("energy", 3))
    st.caption(ENERGY_LABELS.get(energy, ""))

    st.markdown("---")

    # ── Sleep ─────────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Sleep</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        sleep_hours = st.number_input(
            "Hours slept", 0.0, 14.0,
            float(existing.get("sleep_hours", 7.0)), 0.5,
        )
    with c2:
        sleep_quality = st.slider("Sleep quality", 1, 5, existing.get("sleep_quality", 3))
        st.caption(SLEEP_LABELS.get(sleep_quality, ""))

    st.markdown("---")

    # ── Pain ──────────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Pain</div>', unsafe_allow_html=True)
    pain = st.slider("Overall pain level (0 = None, 10 = Severe)", 0, 10, existing.get("pain", 0))

    st.markdown("---")

    # ── Symptoms ──────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Symptoms</div>', unsafe_allow_html=True)
    st.caption("Select any symptoms you have experienced today. Leave blank if none.")

    existing_symptoms = existing.get("symptoms", {})
    st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
    selected_symptoms = st.multiselect(
        "Symptoms",
        SYMPTOMS,
        default=[s for s in existing_symptoms.keys() if s in SYMPTOMS],
        format_func=lambda x: x.capitalize(),
        label_visibility="collapsed",
    )

    symptom_severities = {}
    if selected_symptoms:
        st.markdown("**Rate the severity of each symptom** (1 = mild, 5 = severe)")
        st.markdown("")

        if "bleeding" in selected_symptoms:
            st.markdown(
                '<div class="alert-card">Bleeding has been logged. '
                'Please contact your healthcare provider.</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

        cols = st.columns(min(len(selected_symptoms), 3))
        for i, sym in enumerate(selected_symptoms):
            with cols[i % 3]:
                sev = st.slider(
                    sym.capitalize(), 1, 5,
                    existing_symptoms.get(sym, 2),
                    key=f"sev_{sym}",
                )
                symptom_severities[sym] = sev

    st.markdown("---")

    # ── Wellness checklist ────────────────────────────────────────────────
    st.markdown('<div class="card-title">Wellness Checklist</div>', unsafe_allow_html=True)

    hydration_idx = existing.get("hydration", 2) - 1
    hydration_label = st.select_slider(
        "Hydration today",
        HYDRATION_LABELS,
        value=HYDRATION_LABELS[max(0, min(hydration_idx, 2))],
    )

    st.markdown('<div style="margin-top:0.75rem"></div>', unsafe_allow_html=True)
    movement = st.checkbox("Light movement / exercise", value=existing.get("movement", False))
    ate_well = st.checkbox("Ate regular meals", value=existing.get("ate_well", False))

    st.markdown("---")

    # ── Prenatal vitamins ─────────────────────────────────────────────────
    st.markdown('<div class="card-title">Prenatal Vitamins Taken Today</div>', unsafe_allow_html=True)
    st.caption("Check each supplement you have taken today.")

    existing_vitamins = existing.get("vitamins", {})
    # backwards compat: if stored as a bool from old logs, treat as all-false
    if isinstance(existing_vitamins, bool):
        existing_vitamins = {}

    vitamin_cols = st.columns(2)
    vitamin_values = {}
    for i, (key, label) in enumerate(PRENATAL_VITAMINS):
        with vitamin_cols[i % 2]:
            vitamin_values[key] = st.checkbox(
                label,
                value=existing_vitamins.get(key, False),
                key=f"vit_{key}",
            )

    st.markdown("---")

    # ── Notes ─────────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Notes</div>', unsafe_allow_html=True)
    notes = st.text_area(
        "Anything else on your mind today?",
        value=existing.get("notes", ""),
        height=100,
        placeholder="How was your day? Any concerns, wins, or moments to remember...",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save Today's Log", use_container_width=True):
        hydration_map = {"Poor": 1, "Okay": 2, "Good": 3}
        log = {
            "mood":          mood,
            "energy":        energy,
            "sleep_hours":   sleep_hours,
            "sleep_quality": sleep_quality,
            "pain":          pain,
            "symptoms":      symptom_severities,
            "vitamins":      vitamin_values,
            "movement":      movement,
            "ate_well":      ate_well,
            "hydration":     hydration_map[hydration_label],
            "notes":         notes,
        }
        dm.save_daily_log(log)
        score = compute_daily_score(log)
        label = score_label(score)
        st.success(f"Saved. Today's wellness score: {score}/100 — {label}")
        st.balloons()