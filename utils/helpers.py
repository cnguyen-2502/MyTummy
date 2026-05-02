from datetime import date, datetime, timedelta

def get_week_of_pregnancy(due_date_str: str):
    """Returns (week, extra_days) given a due date string."""
    due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    conception = due - timedelta(weeks=40)
    today = date.today()
    delta = today - conception
    total_days = delta.days
    week = total_days // 7
    days = total_days % 7
    week = max(1, min(week, 42))
    return week, days

def get_trimester(week: int) -> str:
    if week <= 13:
        return "1st Trimester"
    elif week <= 26:
        return "2nd Trimester"
    else:
        return "3rd Trimester"

def trimester_class(week: int) -> str:
    if week <= 13: return "t1"
    elif week <= 26: return "t2"
    return "t3"

def compute_daily_score(log: dict) -> int:
    """
    Compute a composite wellness score (0-100).

    Weighting rationale:
      - Energy and mood are the strongest day-to-day indicators of wellbeing (up to +/-12 each)
      - Sleep quantity and quality together can swing the score significantly (up to +/-16)
      - Pain is penalised proportionally — high pain dominates the day (up to -20)
      - Positive behaviours (vitamins, hydration, movement) provide modest bonuses
      - Symptoms are penalised by severity; bleeding is treated as a hard deduction
    """
    score = 50

    # Energy (1–5); each point above/below 3 = +/-8
    energy = log.get("energy", 3)
    score += (energy - 3) * 8

    # Mood (1–5; 5 = very calm/positive); each point = +/-6
    mood = log.get("mood", 3)
    score += (mood - 3) * 6

    # Sleep hours
    sleep_h = log.get("sleep_hours", 7)
    if sleep_h >= 9:
        score += 8
    elif sleep_h >= 7:
        score += 5
    elif sleep_h >= 6:
        score += 0
    elif sleep_h >= 5:
        score -= 6
    else:
        score -= 12

    # Sleep quality (1–5)
    sleep_q = log.get("sleep_quality", 3)
    score += (sleep_q - 3) * 4

    # Pain (0–10); penalised steeply at high levels
    pain = log.get("pain", 0)
    if pain <= 2:
        score -= pain * 1
    elif pain <= 5:
        score -= 2 + (pain - 2) * 3
    else:
        score -= 11 + (pain - 5) * 4  # max deduction = -20 at pain=10 (approx)

    # Prenatal vitamins — now stored as a dict of {vitamin_key: bool}
    # Awards +1 per vitamin taken (up to +5), backwards compat with old bool format
    vitamins = log.get("vitamins", {})
    if isinstance(vitamins, bool):
        score += 5 if vitamins else 0
    elif isinstance(vitamins, dict):
        taken = sum(1 for v in vitamins.values() if v)
        score += taken  # +1 per vitamin taken, max +5

    # Hydration (1 = poor, 2 = okay, 3 = good)
    hydration = log.get("hydration", 2)
    if hydration == 3:
        score += 6
    elif hydration == 1:
        score -= 6

    # Light movement or exercise
    if log.get("movement"):
        score += 4

    # Ate regular meals
    if log.get("ate_well"):
        score += 4

    # Symptoms — each symptom penalised by its recorded severity (1–5)
    symptoms = log.get("symptoms", {})
    for sym, sev in symptoms.items():
        if sym == "bleeding":
            score -= 20  # hard deduction regardless of severity
        elif sym in ("severe_headache", "chest_pain", "vision_changes"):
            score -= sev * 5  # high-risk symptoms weighted more heavily
        else:
            score -= sev * 2

    return max(0, min(100, int(score)))

def score_color(score: int) -> str:
    if score >= 75: return "#5da05d"
    if score >= 50: return "#E8A030"
    return "#D94F4F"

def score_label(score: int) -> str:
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 55: return "Fair"
    if score >= 40: return "Low"
    return "Needs care"


FETAL_MILESTONES = {
    # 1st Trimester
    4:  "Embryo has implanted in the uterine wall",
    5:  "Heart begins to form — a tiny tube that will become the heart",
    6:  "Heart starts beating; brain and spinal cord taking shape",
    7:  "Arms and leg buds appear; face features beginning to form",
    8:  "Fingers and toes forming; all major organs have begun developing",
    9:  "Embryo is now a fetus; tail disappears; eyelids form",
    10: "Brain growing rapidly; baby can make small movements",
    11: "Fingernails developing; baby can open and close fists",
    12: "End of 1st trimester — miscarriage risk drops significantly; reflexes developing",
    13: "Vocal cords forming; intestines moving into position",
    # 2nd Trimester
    14: "Baby's facial muscles allow for expressions; sucking reflex present",
    15: "Bones hardening; baby may sense light through closed eyelids",
    16: "Baby can hear muffled sounds from outside the womb",
    17: "Fat starting to form under the skin; skeleton solidifying",
    18: "Baby is yawning, hiccupping, and rolling; ideal time for anatomy scan",
    19: "Vernix caseosa (protective coating) covers skin",
    20: "Halfway there — baby is roughly the size of a banana",
    21: "Eyebrows and eyelashes present; swallowing amniotic fluid regularly",
    22: "Sense of touch developing; lips and eyes more defined",
    23: "Lungs producing surfactant in preparation for breathing",
    24: "Viability milestone — baby has a chance of survival if born now",
    25: "Responding more to sounds; brain developing rapidly",
    26: "Eyes beginning to open; immune system strengthening",
    # 3rd Trimester
    27: "Start of 3rd trimester; brain can now regulate body temperature",
    28: "Baby opens eyes and can distinguish light from dark",
    29: "Muscles and lungs maturing; baby gaining weight quickly",
    30: "Brain developing folds; bone marrow now making red blood cells",
    31: "All five senses functioning; baby processes information and dreams",
    32: "Baby likely in head-down position; practice breathing movements",
    33: "Skull remains soft for delivery; immune system boosted via placenta",
    34: "Fingernails reach fingertips; central nervous system maturing",
    35: "Kidneys fully developed; liver can process some waste",
    36: "Full term approaching — most systems ready for life outside",
    37: "Full term — baby considered ready to be born",
    38: "Brain and lungs continue maturing right up until birth",
    39: "Placenta delivering antibodies to support baby's immune system",
    40: "Due date week — baby is fully developed and ready to meet you",
}


SYMPTOM_FLAGS = {
    "bleeding": (
        "Any bleeding should be reported to your doctor or midwife promptly.",
        "danger"
    ),
    "severe_headache": (
        "A severe or persistent headache can be a sign of preeclampsia. Check your blood pressure and contact your provider.",
        "warning"
    ),
    "vision_changes": (
        "Blurred vision or seeing spots may indicate high blood pressure. Seek advice from your provider today.",
        "danger"
    ),
    "chest_pain": (
        "Chest pain or difficulty breathing warrants immediate medical attention.",
        "danger"
    ),
    "reduced_movement": (
        "If you notice reduced fetal movement, contact your midwife or maternity unit straight away.",
        "danger"
    ),
    "swelling": (
        "Sudden or severe swelling in hands, face, or feet can be a sign of preeclampsia.",
        "warning"
    ),
}


TRIMESTER_INFO = {
    "1st Trimester": {
        "weeks": "Weeks 1–13",
        "focus": (
            "The most critical period for organ formation. The neural tube, heart, and all major "
            "organs begin developing. Focus on avoiding teratogens, starting prenatal vitamins, "
            "and managing nausea."
        ),
        "nutrition": [
            "Folic acid (400–800mcg daily) — crucial for neural tube development",
            "Iron — supports increased blood volume",
            "Vitamin D — bone and immune development",
            "Vitamin B6 — can help reduce nausea",
            "Iodine — supports thyroid and brain development",
            "Avoid alcohol, raw fish, unpasteurised dairy, and high-mercury fish",
            "Limit caffeine to under 200mg per day",
        ],
        "common_symptoms": [
            "Nausea / morning sickness",
            "Fatigue",
            "Breast tenderness",
            "Frequent urination",
            "Food aversions",
            "Heightened sense of smell",
            "Bloating",
            "Light spotting (implantation)",
            "Mood swings",
        ],
        "appointments": [
            "First prenatal booking appointment (8–10 weeks)",
            "Dating / nuchal translucency ultrasound (11–14 weeks)",
            "First trimester screening bloodwork",
        ],
        "warning_signs": [
            "Heavy bleeding",
            "Severe one-sided pain (rule out ectopic pregnancy)",
            "High fever",
        ],
    },
    "2nd Trimester": {
        "weeks": "Weeks 14–26",
        "focus": (
            "Often called the 'honeymoon trimester' — nausea typically eases and energy returns. "
            "Baby grows rapidly, you'll feel the first movements (quickening), and the anatomy scan "
            "provides a detailed check on development."
        ),
        "nutrition": [
            "Calcium (1,000mg/day) — for bone and teeth development",
            "Iron (27mg/day) — anaemia risk increases in 2nd trimester",
            "Omega-3 fatty acids (DHA) — brain and eye development",
            "Protein (75–100g/day) — supports rapid fetal growth",
            "Magnesium — helps with leg cramps",
            "Vitamin C — aids iron absorption",
            "Continue prenatal vitamin with folic acid",
        ],
        "common_symptoms": [
            "Round ligament pain",
            "Back pain",
            "Heartburn / acid reflux",
            "Leg cramps",
            "Nasal congestion",
            "Skin changes (linea nigra, melasma)",
            "Mild swelling in feet and ankles",
            "Braxton Hicks (later in trimester)",
        ],
        "appointments": [
            "Anatomy scan / mid-pregnancy ultrasound (18–22 weeks)",
            "Glucose challenge screening (24–28 weeks)",
            "Routine prenatal checks every 4 weeks",
            "Quad screen / genetic screening bloodwork if indicated",
        ],
        "warning_signs": [
            "Significant bleeding",
            "Severe abdominal pain",
            "Signs of preeclampsia (headache, vision changes, rapid swelling)",
            "Fluid leaking from vagina before 37 weeks",
        ],
    },
    "3rd Trimester": {
        "weeks": "Weeks 27–40",
        "focus": (
            "Baby is gaining weight and maturing rapidly. Focus on monitoring fetal movement (kick counts), "
            "preparing for birth, and watching for signs of labour. Your body is preparing for delivery "
            "— rest when you can and stay in close contact with your provider."
        ),
        "nutrition": [
            "Extra calories (+300/day above pre-pregnancy baseline)",
            "Calcium — bones and teeth are mineralising rapidly",
            "Iron — continue supplementing to prevent anaemia",
            "Vitamin K — important for blood clotting at delivery",
            "Stay well hydrated (8–10 glasses of water/day)",
            "Smaller, more frequent meals to ease heartburn and pressure",
            "Fibre — to manage constipation as baby presses on bowel",
        ],
        "common_symptoms": [
            "Shortness of breath",
            "Heartburn",
            "Pelvic pressure / lightning crotch",
            "Swelling (oedema) in feet, ankles, and hands",
            "Frequent urination",
            "Insomnia",
            "Braxton Hicks contractions",
            "Back and hip pain",
            "Colostrum leaking from breasts",
        ],
        "appointments": [
            "Prenatal visits every 2 weeks (28–36 weeks), then weekly (36+ weeks)",
            "Group B Strep (GBS) swab (35–37 weeks)",
            "Non-stress test (NST) if post-dates or high risk",
            "Growth scan if indicated",
            "Birth plan discussion with provider",
        ],
        "warning_signs": [
            "Reduced or absent fetal movement — contact your midwife immediately",
            "Signs of preeclampsia (severe headache, vision changes, upper right pain, sudden swelling)",
            "Regular painful contractions before 37 weeks (preterm labour)",
            "Gush or continuous trickle of fluid (waters breaking)",
            "Vaginal bleeding",
        ],
    },
}