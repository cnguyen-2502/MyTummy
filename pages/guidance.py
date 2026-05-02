import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from utils.helpers import get_week_of_pregnancy, get_trimester, TRIMESTER_INFO

GUIDANCE_CONTENT = {
    "1st Trimester": {
        "nutrition": [
            ("Folic Acid (400–800 mcg/day)", "Critical for neural tube development. Found in leafy greens, fortified cereals, and supplements.", "WHO"),
            ("Iron (27 mg/day)", "Supports increased blood volume. Sources: lean meat, beans, fortified grains. Take with vitamin C for absorption.", "CDC"),
            ("Avoid alcohol completely", "No safe level of alcohol in pregnancy. Alcohol crosses the placenta and can cause fetal alcohol spectrum disorders.", "ACOG"),
            ("Limit caffeine to under 200mg/day", "Moderate caffeine restriction is recommended. One 12oz coffee generally falls within the limit.", "ACOG"),
            ("Food safety", "Avoid raw fish, undercooked meat, unpasteurised dairy, and deli meats. These may carry Listeria or Toxoplasma.", "CDC"),
        ],
        "symptoms": [
            ("Nausea and vomiting", "Common in the first trimester. Eat small, frequent meals. Ginger tea may help. Contact your provider if severe.", "WHO"),
            ("Fatigue", "Normal as your body works hard to form the placenta. Rest when possible — light exercise can help energy levels.", "ACOG"),
            ("Breast tenderness", "Hormonal changes cause breast growth and sensitivity. A supportive bra may help.", "CDC"),
            ("Frequent urination", "Increased blood flow to kidneys is normal. Stay hydrated — do not cut back on fluids.", "CDC"),
        ],
        "warning_signs": [
            "Heavy bleeding or passing tissue",
            "Severe abdominal pain or cramping",
            "High fever (above 100.4°F / 38°C)",
            "Painful urination (may indicate a UTI)",
        ],
        "image": "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=800&q=80",
        "image_caption": "First trimester — weeks 1 to 13",
    },
    "2nd Trimester": {
        "nutrition": [
            ("Calcium (1000 mg/day)", "Supports baby's bone development. Sources: dairy, fortified plant milks, broccoli, sardines.", "WHO"),
            ("Protein (75–100g/day)", "Critical for fetal growth. Include eggs, lean meat, legumes, and dairy in each meal.", "ACOG"),
            ("Omega-3 fatty acids", "DHA supports brain and eye development. Safe sources: low-mercury fish such as salmon and sardines, walnuts, DHA supplements.", "CDC"),
            ("Iron", "Anaemia risk increases. Continue iron-rich foods and discuss supplementation with your provider.", "WHO"),
        ],
        "symptoms": [
            ("Round ligament pain", "Sharp pains on the sides of the abdomen as ligaments stretch. Normal, but mention to your provider if persistent.", "ACOG"),
            ("Back pain", "Weight shifts your centre of gravity. Prenatal yoga, swimming, and supportive footwear can help.", "CDC"),
            ("Heartburn", "Baby pushes on the stomach. Eat smaller meals, avoid spicy foods, and do not lie down right after eating.", "WHO"),
            ("Leg cramps", "Often from calcium and magnesium needs. Stretching before bed and staying hydrated helps.", "ACOG"),
        ],
        "warning_signs": [
            "Bleeding or fluid leakage",
            "Severe headache or vision changes",
            "Sudden swelling of face, hands, or feet",
            "Fewer than 10 fetal movements in 2 hours (after week 20)",
            "Fever above 100.4°F",
        ],
        "image": "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=800&q=80",
        "image_caption": "Second trimester — weeks 14 to 26",
    },
    "3rd Trimester": {
        "nutrition": [
            ("Extra 300 calories per day", "Fetal brain growth is rapid. Focus on nutrient-dense foods rather than empty calories.", "WHO"),
            ("Continue calcium and iron", "Baby stores iron reserves for the first 6 months of life. Keep up supplementation.", "CDC"),
            ("Stay well hydrated", "Dehydration can trigger Braxton Hicks contractions. Aim for 8 to 10 cups of water daily.", "ACOG"),
            ("Vitamin K and fibre", "Prepare for delivery by eating leafy greens and adequate fibre to support digestion.", "WHO"),
        ],
        "symptoms": [
            ("Braxton Hicks contractions", "Irregular practice contractions. Unlike true labour, they do not increase in frequency or intensity.", "ACOG"),
            ("Swelling (oedema)", "Normal in feet and ankles. Elevate feet and avoid prolonged standing. Sudden facial swelling — contact your doctor.", "CDC"),
            ("Shortness of breath", "Baby is pressing on the diaphragm. Sleep propped up and avoid large meals before bed.", "WHO"),
            ("Insomnia", "Discomfort, frequent urination, and anxiety are common. A pregnancy pillow, cool room, and relaxation techniques can help.", "ACOG"),
        ],
        "warning_signs": [
            "Preeclampsia signs: severe headache, vision changes, upper abdominal pain, sudden swelling",
            "Regular contractions before 37 weeks (preterm labour)",
            "Decreased fetal movement",
            "Vaginal bleeding",
            "Water breaking",
        ],
        "image": "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=800&q=80",
        "image_caption": "Third trimester — weeks 27 to 40",
    },
}

SOURCES = {
    "WHO":  ("World Health Organization", "https://www.who.int/health-topics/maternal-health"),
    "CDC":  ("Centers for Disease Control and Prevention", "https://www.cdc.gov/pregnancy/index.html"),
    "ACOG": ("American College of Obstetricians and Gynecologists", "https://www.acog.org/womens-health/pregnancy"),
}

# Unsplash images for nutrition and symptoms tabs
NUTRITION_IMAGE = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&q=80"
SYMPTOMS_IMAGE  = "https://images.unsplash.com/photo-1576765608535-5f04d1e3f289?w=800&q=80"


def render(dm):
    st.markdown('<div class="page-header">Guidance & Resources</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Evidence-based information from trusted medical sources</div>', unsafe_allow_html=True)

    due_date = st.session_state.get("due_date")
    trimester = "2nd Trimester"
    week = 20
    if due_date:
        week, _ = get_week_of_pregnancy(due_date)
        trimester = get_trimester(week)

    # Source attribution
    st.markdown("""
    <div class="card">
        <div class="card-title">Information Sources</div>
        <div style="font-size:0.83rem;color:var(--text-muted)">
            All guidance below is curated from the
            <b>World Health Organization (WHO)</b>,
            <b>Centers for Disease Control and Prevention (CDC)</b>, and the
            <b>American College of Obstetricians and Gynecologists (ACOG)</b>.<br><br>
            <i>This is informational only — always consult your healthcare provider.</i>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Flags from today's log
    from datetime import date
    today_log = dm.get_daily_log_for(str(date.today()))
    if today_log:
        syms = today_log.get("symptoms", {})
        pain = today_log.get("pain", 0)
        _show_flags(syms, pain, week)

    # Trimester selector
    selected_trimester = st.selectbox(
        "View guidance for:",
        ["1st Trimester", "2nd Trimester", "3rd Trimester"],
        index=["1st Trimester", "2nd Trimester", "3rd Trimester"].index(trimester),
        key="trimester_selector",
    )

    guidance = GUIDANCE_CONTENT[selected_trimester]

    # Hero image for selected trimester
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="border-radius:16px;overflow:hidden;margin-bottom:0.5rem;max-height:220px">
        <img src="{guidance['image']}"
             style="width:100%;height:220px;object-fit:cover;display:block" />
    </div>
    <div style="font-size:0.78rem;color:var(--text-muted);text-align:right;margin-bottom:1rem">
        {guidance['image_caption']}
        {f' &nbsp;·&nbsp; <b>You are here — Week {week}</b>' if due_date and selected_trimester == trimester else ''}
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Nutrition", "Symptoms", "Warning Signs"])

    with tab1:
        st.markdown(f"""
        <div style="border-radius:12px;overflow:hidden;margin-bottom:1.25rem;max-height:160px">
            <img src="{NUTRITION_IMAGE}" style="width:100%;height:160px;object-fit:cover;display:block" />
        </div>
        """, unsafe_allow_html=True)

        for title, desc, source in guidance["nutrition"]:
            st.markdown(f"""
            <div class="card">
                <div class="card-title" style="justify-content:space-between">
                    {title}
                    <span style="font-size:0.7rem;color:var(--text-muted);font-weight:400">{source}</span>
                </div>
                <div style="font-size:0.87rem;color:var(--text)">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown(f"""
        <div style="border-radius:12px;overflow:hidden;margin-bottom:1.25rem;max-height:160px">
            <img src="{SYMPTOMS_IMAGE}" style="width:100%;height:160px;object-fit:cover;display:block" />
        </div>
        """, unsafe_allow_html=True)

        for title, desc, source in guidance["symptoms"]:
            st.markdown(f"""
            <div class="card">
                <div class="card-title" style="justify-content:space-between">
                    {title}
                    <span style="font-size:0.7rem;color:var(--text-muted);font-weight:400">{source}</span>
                </div>
                <div style="font-size:0.87rem;color:var(--text)">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("""
        <div class="alert-card">
            <b>Contact your doctor or go to the emergency room if you experience any of the following:</b>
        </div>
        """, unsafe_allow_html=True)

        for sign in guidance["warning_signs"]:
            st.markdown(f"""
            <div style="border-left:3px solid var(--danger);padding:0.5rem 0.75rem;
                        margin-bottom:0.4rem;background:var(--danger-bg);
                        border-radius:0 8px 8px 0;font-size:0.87rem">
                {sign}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">When to call vs. when to go to the ER</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="card" style="border-color:var(--warning)">
                <div class="card-title">Call your provider</div>
                <div style="font-size:0.85rem;line-height:1.9">
                    Mild spotting<br>
                    Mild headache that resolves<br>
                    Questions about symptoms<br>
                    Signs of a UTI<br>
                    Mild swelling in feet
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="card" style="border-color:var(--danger)">
                <div class="card-title">Go to the ER</div>
                <div style="font-size:0.85rem;line-height:1.9">
                    Heavy bleeding<br>
                    Severe chest pain<br>
                    Sudden vision loss<br>
                    Seizures<br>
                    Suspected water breaking
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Kick count guide
    if week >= 20:
        st.markdown("---")
        st.markdown('<div class="card-title">Kick Count Guide</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div style="font-size:0.87rem;line-height:1.9">
                <b>How to do a kick count (from week 28 onwards):</b><br><br>
                1. Choose a consistent time each day — baby is often most active after meals.<br>
                2. Sit or lie comfortably and count each movement: kick, roll, jab, or swish.<br>
                3. Record how long it takes to reach 10 movements.<br>
                4. Contact your provider if you do not feel 10 movements within 2 hours.<br><br>
                <span style="color:var(--text-muted);font-size:0.82rem">Source: ACOG and CDC</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Trusted links
    st.markdown("---")
    st.markdown('<div class="card-title">Trusted Resources</div>', unsafe_allow_html=True)
    for code, (name, url) in SOURCES.items():
        st.markdown(f"- [{name}]({url})")


def _show_flags(symptoms, pain, week):
    if "bleeding" in symptoms:
        st.markdown("""
        <div class="alert-card">
            <b>Bleeding was logged today.</b> Please contact your healthcare provider immediately.
            Bleeding in pregnancy always warrants medical evaluation.
        </div>
        """, unsafe_allow_html=True)

    if "headache" in symptoms and symptoms.get("headache", 0) >= 3:
        st.markdown("""
        <div class="warning-card">
            <b>Severe headache noted.</b> Persistent or severe headaches during pregnancy —
            especially in the 2nd or 3rd trimester — can be a sign of preeclampsia.
            Consider contacting your doctor, especially if accompanied by vision changes or swelling.
        </div>
        """, unsafe_allow_html=True)

    if pain >= 7:
        st.markdown(f"""
        <div class="warning-card">
            <b>High pain level ({pain}/10) logged.</b> If pain is sudden, severe, or localised to your
            abdomen or chest, seek medical attention promptly.
        </div>
        """, unsafe_allow_html=True)