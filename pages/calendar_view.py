import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from datetime import date, datetime, timedelta
import calendar
from utils.helpers import compute_daily_score, score_color, score_label, get_week_of_pregnancy

MOOD_LABELS  = {1: "Very stressed", 2: "Stressed", 3: "Neutral", 4: "Calm", 5: "Very calm"}
SLEEP_LABELS = {1: "Awful", 2: "Poor", 3: "Okay", 4: "Good", 5: "Great"}
MOOD_EMOJI   = {1: "😟", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}

SYMPTOM_OPTIONS  = [
    "nausea", "headache", "back_pain", "swelling",
    "heartburn", "fatigue", "bleeding", "cramping",
]
HYDRATION_LABELS = ["Poor", "Okay", "Good"]

PRENATAL_VITAMINS = [
    ("folic_acid",    "Folic acid (400–800 mcg)"),
    ("iron",          "Iron (27 mg)"),
    ("calcium_vit_d", "Calcium & Vitamin D"),
    ("iodine",        "Iodine"),
    ("dha_omega3",    "DHA / Omega-3"),
]


def _entry_form(dm, prefill: dict, form_date: str, form_key: str):
    """Renders the shared add/edit form and saves on submit."""
    today = date.today()

    entry_date = st.date_input(
        "Entry date",
        value=datetime.strptime(form_date, "%Y-%m-%d").date() if form_date else today,
        key=f"{form_key}_date",
    )

    col1, col2 = st.columns(2)
    with col1:
        mood = st.slider(
            "Mood (1 = Very stressed, 5 = Very calm)", 1, 5,
            prefill.get("mood", 3), key=f"{form_key}_mood",
        )
        energy = st.slider(
            "Energy (1 = Exhausted, 5 = Great)", 1, 5,
            prefill.get("energy", 3), key=f"{form_key}_energy",
        )
        pain = st.slider(
            "Pain level (0 = None, 10 = Severe)", 0, 10,
            prefill.get("pain", 0), key=f"{form_key}_pain",
        )
    with col2:
        sleep_h = st.number_input(
            "Sleep hours", 0.0, 14.0,
            float(prefill.get("sleep_hours", 7.0)), 0.5,
            key=f"{form_key}_sleep_h",
        )
        sleep_q = st.slider(
            "Sleep quality (1 = Awful, 5 = Great)", 1, 5,
            prefill.get("sleep_quality", 3), key=f"{form_key}_sleep_q",
        )
        hydration_idx = prefill.get("hydration", 2) - 1
        hydration = st.select_slider(
            "Hydration", HYDRATION_LABELS,
            HYDRATION_LABELS[max(0, min(hydration_idx, 2))],
            key=f"{form_key}_hydration",
        )

    existing_syms = list(prefill.get("symptoms", {}).keys())
    selected_syms = st.multiselect(
        "Symptoms", SYMPTOM_OPTIONS,
        default=[s for s in existing_syms if s in SYMPTOM_OPTIONS],
        key=f"{form_key}_symptoms",
    )

    sym_dict = {}
    if selected_syms:
        sev_cols = st.columns(min(len(selected_syms), 3))
        for i, s in enumerate(selected_syms):
            with sev_cols[i % len(sev_cols)]:
                default_sev = prefill.get("symptoms", {}).get(s, 3)
                sym_dict[s] = st.slider(
                    s.replace("_", " ").capitalize(),
                    1, 5, default_sev,
                    key=f"{form_key}_sev_{s}",
                )

    st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
    movement = st.checkbox(
        "Light movement / exercise",
        value=prefill.get("movement", False),
        key=f"{form_key}_movement",
    )
    ate_well = st.checkbox(
        "Ate regular meals",
        value=prefill.get("ate_well", False),
        key=f"{form_key}_ate",
    )

    # Prenatal vitamins
    st.markdown('<div style="margin-top:0.75rem;font-weight:500;font-size:0.9rem">Prenatal vitamins taken today</div>', unsafe_allow_html=True)
    existing_vitamins = prefill.get("vitamins", {})
    if isinstance(existing_vitamins, bool):
        existing_vitamins = {}

    vit_cols = st.columns(2)
    vitamin_values = {}
    for i, (key, label) in enumerate(PRENATAL_VITAMINS):
        with vit_cols[i % 2]:
            vitamin_values[key] = st.checkbox(
                label,
                value=existing_vitamins.get(key, False),
                key=f"{form_key}_vit_{key}",
            )

    notes = st.text_area(
        "Notes / how are you feeling?", prefill.get("notes", ""),
        key=f"{form_key}_notes",
    )

    if st.button("Save entry", key=f"{form_key}_save", use_container_width=True):
        hydration_map = {"Poor": 1, "Okay": 2, "Good": 3}
        new_log = {
            "mood":          mood,
            "energy":        energy,
            "sleep_hours":   sleep_h,
            "sleep_quality": sleep_q,
            "pain":          pain,
            "symptoms":      sym_dict,
            "vitamins":      vitamin_values,
            "movement":      movement,
            "ate_well":      ate_well,
            "hydration":     hydration_map[hydration],
            "notes":         notes,
        }
        dm.save_daily_log(new_log, target_date=str(entry_date))
        st.success(f"Entry saved for {entry_date.strftime('%A, %B %-d, %Y')}!")
        st.session_state.selected_date = str(entry_date)
        st.session_state.cal_year  = entry_date.year
        st.session_state.cal_month = entry_date.month
        st.rerun()


def render(dm):
    st.markdown('<div class="page-header">My Journal</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">A month-by-month view of your journey</div>', unsafe_allow_html=True)

    due_date = st.session_state.get("due_date")
    all_logs = dm.get_daily_logs()
    log_by_date = {l.get("date", ""): l for l in all_logs}

    # ── Month navigation ───────────────────────────────────────────────────
    today = date.today()
    if "cal_year"      not in st.session_state: st.session_state.cal_year      = today.year
    if "cal_month"     not in st.session_state: st.session_state.cal_month     = today.month
    if "selected_date" not in st.session_state: st.session_state.selected_date = None

    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
    with nav_col1:
        if st.button("◀", use_container_width=True, key="prev_month"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.session_state.selected_date = None
            st.rerun()
    with nav_col2:
        month_name = datetime(st.session_state.cal_year, st.session_state.cal_month, 1).strftime("%B %Y")
        st.markdown(
            f'<div style="text-align:center;font-size:1.15rem;font-weight:700;'
            f'color:var(--mauve);padding:0.4rem 0">{month_name}</div>',
            unsafe_allow_html=True,
        )
    with nav_col3:
        if st.button("▶", use_container_width=True, key="next_month"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.session_state.selected_date = None
            st.rerun()

    # ── Calendar grid ──────────────────────────────────────────────────────
    year  = st.session_state.cal_year
    month = st.session_state.cal_month
    cal   = calendar.monthcalendar(year, month)
    days_in_month = calendar.monthrange(year, month)[1]

    month_scores = {}
    for day in range(1, days_in_month + 1):
        ds = f"{year}-{month:02d}-{day:02d}"
        if ds in log_by_date:
            month_scores[day] = compute_daily_score(log_by_date[ds])

    day_headers = "".join(
        f'<div class="cal-dow">{d}</div>'
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )

    cells = ""
    for week in cal:
        for day in week:
            if day == 0:
                cells += '<div class="cal-cell cal-empty"></div>'
            else:
                ds           = f"{year}-{month:02d}-{day:02d}"
                is_today     = (day == today.day and month == today.month and year == today.year)
                is_selected  = (st.session_state.selected_date == ds)
                has_log      = ds in log_by_date
                has_bleeding = has_log and "bleeding" in log_by_date[ds].get("symptoms", {})

                dot_html = score_badge = ""
                if has_log:
                    sc  = month_scores[day]
                    col = score_color(sc)
                    dot_html    = f'<div class="cal-dot" style="background:{col}"></div>'
                    score_badge = f'<div class="cal-score" style="color:{col}">{sc}</div>'

                bleeding_badge = '<div class="cal-bleed">&#9888;</div>' if has_bleeding else ""
                today_cls = " cal-today"    if is_today    else ""
                sel_cls   = " cal-selected" if is_selected else ""
                log_cls   = " cal-has-log"  if has_log     else ""

                cells += (
                    f'<div class="cal-cell{today_cls}{sel_cls}{log_cls}" data-date="{ds}">'
                    f'<div class="cal-day-num">{day}</div>'
                    f'{dot_html}{score_badge}{bleeding_badge}'
                    f'</div>'
                )

    legend_html = """
    <div class="cal-legend">
        <span class="legend-item"><span class="legend-dot" style="background:#e0737d"></span>Poor (1&ndash;39)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#f0a500"></span>Fair (40&ndash;69)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#5cb85c"></span>Good (70&ndash;100)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#ccc"></span>Today</span>
    </div>
    """

    full_cal_html = f"""
    <style>
    .cal-wrap {{ background:var(--cream-dark,#fdf6f0);border-radius:16px;padding:1rem;
                box-shadow:0 2px 12px rgba(0,0,0,0.07);margin-bottom:1rem; }}
    .cal-grid {{ display:grid;grid-template-columns:repeat(7,1fr);gap:4px; }}
    .cal-dow  {{ text-align:center;font-size:0.7rem;font-weight:700;color:var(--text-muted,#999);
                letter-spacing:0.05em;padding:0.3rem 0;text-transform:uppercase; }}
    .cal-cell {{ position:relative;aspect-ratio:1;border-radius:10px;display:flex;
                flex-direction:column;align-items:center;justify-content:flex-start;
                padding:4px 2px 2px;cursor:default;border:2px solid transparent;
                transition:border-color .15s,background .15s;min-height:52px; }}
    .cal-cell.cal-has-log  {{ background:var(--cream,#fff8f3);cursor:pointer; }}
    .cal-cell.cal-has-log:hover {{ border-color:var(--mauve,#b07fa0);background:#f5eaf2; }}
    .cal-cell.cal-today    {{ border-color:var(--mauve,#b07fa0)!important;background:#f5eaf222; }}
    .cal-cell.cal-selected {{ border-color:var(--mauve,#b07fa0)!important;background:#ede0ea!important; }}
    .cal-cell.cal-empty    {{ background:transparent;border:none;cursor:default; }}
    .cal-day-num {{ font-size:0.78rem;font-weight:600;color:var(--text,#444);line-height:1;margin-bottom:2px; }}
    .cal-dot     {{ width:8px;height:8px;border-radius:50%;margin-top:2px; }}
    .cal-score   {{ font-size:0.65rem;font-weight:700;margin-top:1px; }}
    .cal-bleed   {{ position:absolute;top:1px;right:3px;font-size:0.55rem;line-height:1; }}
    .cal-legend  {{ display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;
                   margin-top:0.75rem;font-size:0.73rem;color:var(--text-muted,#999); }}
    .legend-item {{ display:flex;align-items:center;gap:4px; }}
    .legend-dot  {{ width:8px;height:8px;border-radius:50%;display:inline-block; }}
    </style>
    <div class="cal-wrap">
        <div class="cal-grid">
            {day_headers}
            {cells}
        </div>
        {legend_html}
    </div>
    """
    st.markdown(full_cal_html, unsafe_allow_html=True)

    # ── Date selector ──────────────────────────────────────────────────────
    month_logged = sorted([
        ds for ds in log_by_date if ds.startswith(f"{year}-{month:02d}-")
    ], reverse=True)

    if month_logged:
        def fmt_date(ds):
            try:
                d_obj = datetime.strptime(ds, "%Y-%m-%d").date()
                label = "Today" if d_obj == today else d_obj.strftime("%A %-d")
                sc    = compute_daily_score(log_by_date[ds])
                return f"{label}  ·  Score {sc}"
            except Exception:
                return ds

        options = ["— Select a day —"] + month_logged
        sel_idx = 0
        if st.session_state.selected_date in month_logged:
            sel_idx = month_logged.index(st.session_state.selected_date) + 1

        chosen = st.selectbox(
            "View a logged day this month",
            options,
            index=sel_idx,
            format_func=lambda x: fmt_date(x) if x != "— Select a day —" else x,
            key=f"day_sel_{year}_{month}",
        )
        if chosen != "— Select a day —":
            st.session_state.selected_date = chosen
        else:
            st.session_state.selected_date = None
    else:
        st.markdown(
            '<div style="text-align:center;color:var(--text-muted);font-size:0.88rem;'
            'padding:0.5rem">No entries logged this month yet.</div>',
            unsafe_allow_html=True,
        )

    # ── Detail panel ──────────────────────────────────────────────────────
    sel = st.session_state.selected_date
    if sel and sel in log_by_date:
        log      = log_by_date[sel]
        score    = compute_daily_score(log)
        color    = score_color(score)
        label    = score_label(score)
        mood     = log.get("mood", 3)
        sleep_h  = log.get("sleep_hours", 7)
        sleep_q  = log.get("sleep_quality", 3)
        symptoms = log.get("symptoms", {})
        notes    = log.get("notes", "")
        has_bleeding = "bleeding" in symptoms

        try:
            d_obj      = datetime.strptime(sel, "%Y-%m-%d").date()
            header_day = "Today" if d_obj == today else d_obj.strftime("%A, %B %-d, %Y")
            week_label = ""
            if due_date:
                wk, _      = get_week_of_pregnancy(due_date)
                days_diff  = (today - d_obj).days
                entry_week = wk - (days_diff // 7)
                if 1 <= entry_week <= 42:
                    week_label = f"Week {entry_week} of pregnancy"
        except Exception:
            header_day = sel
            week_label = ""

        st.markdown("<hr style='margin:0.5rem 0'>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem">
            <div>
                <div style="font-size:1.05rem;font-weight:700;color:var(--text)">{header_day}</div>
                <div style="font-size:0.8rem;color:var(--text-muted)">{week_label}</div>
            </div>
            <div style="text-align:center;background:{color}22;border:2px solid {color};
                 border-radius:50%;width:56px;height:56px;display:flex;flex-direction:column;
                 align-items:center;justify-content:center">
                <div style="font-size:1.3rem;font-weight:800;color:{color};line-height:1">{score}</div>
                <div style="font-size:0.55rem;color:{color};font-weight:600;text-transform:uppercase">{label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if has_bleeding:
            st.markdown(
                '<div class="alert-card">Bleeding was logged this day. '
                'Please ensure your provider is aware.</div>',
                unsafe_allow_html=True,
            )

        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown(f"""
            <div style="background:var(--cream-dark);border-radius:12px;padding:0.75rem 1rem;height:100%">
                <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;
                     color:var(--text-muted);margin-bottom:0.4rem">Mood & Sleep</div>
                <div style="font-size:1.4rem;margin-bottom:0.15rem">{MOOD_EMOJI.get(mood, "😐")}</div>
                <div style="font-size:0.85rem"><b>{MOOD_LABELS.get(mood, mood)}</b></div>
                <div style="font-size:0.82rem;color:var(--text-muted);margin-top:0.3rem">
                    {sleep_h}h sleep &middot; {SLEEP_LABELS.get(sleep_q, sleep_q)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with dc2:
            if symptoms:
                sym_html = "".join(
                    f'<span class="stat-pill" style="'
                    f'{"background:#ffd4d4;color:#b94040" if s == "bleeding" else "background:var(--cream);color:var(--mauve)"}'
                    f';margin:2px 2px 2px 0;display:inline-block">'
                    f'{s.capitalize()} ({v}/5)</span>'
                    for s, v in symptoms.items()
                )
                st.markdown(f"""
                <div style="background:var(--cream-dark);border-radius:12px;padding:0.75rem 1rem;height:100%">
                    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;
                         color:var(--text-muted);margin-bottom:0.5rem">Symptoms</div>
                    <div style="display:flex;flex-wrap:wrap">{sym_html}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:var(--cream-dark);border-radius:12px;padding:0.75rem 1rem;height:100%">
                    <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;
                         color:var(--text-muted);margin-bottom:0.5rem">Symptoms</div>
                    <div style="color:var(--text-muted);font-size:0.85rem">None logged</div>
                </div>
                """, unsafe_allow_html=True)

        # Vitamins taken summary
        vitamins_log = log.get("vitamins", {})
        if isinstance(vitamins_log, dict) and any(vitamins_log.values()):
            taken = [label for key, label in PRENATAL_VITAMINS if vitamins_log.get(key)]
            vit_pills = "".join(
                f'<span class="stat-pill" style="background:var(--sage-light);color:#3a6b3a;'
                f'margin:2px 2px 2px 0;display:inline-block">{v}</span>'
                for v in taken
            )
            st.markdown(f"""
            <div style="margin-top:0.75rem;background:var(--cream-dark);border-radius:12px;padding:0.75rem 1rem">
                <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;
                     color:var(--text-muted);margin-bottom:0.5rem">Vitamins taken</div>
                <div style="display:flex;flex-wrap:wrap">{vit_pills}</div>
            </div>
            """, unsafe_allow_html=True)

        if notes:
            st.markdown(f"""
            <div style="margin-top:0.75rem;background:var(--cream-dark);border-left:3px solid var(--mauve);
                 padding:0.65rem 0.9rem;border-radius:0 10px 10px 0;font-size:0.87rem;
                 color:var(--text);font-style:italic">
                "{notes}"
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Edit this entry", expanded=False):
            _entry_form(dm, prefill=log, form_date=sel, form_key=f"edit_{sel}")

    # ── Add entry for any date ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Add entry for a different date", expanded=False):
        _entry_form(dm, prefill={}, form_date=str(today), form_key="add_new")

    # ── Monthly summary strip ──────────────────────────────────────────────
    if month_logged:
        st.markdown("<br>", unsafe_allow_html=True)
        scores_this_month = [compute_daily_score(log_by_date[ds]) for ds in month_logged]
        avg         = sum(scores_this_month) / len(scores_this_month)
        avg_mood_m  = sum(log_by_date[ds].get("mood", 3)        for ds in month_logged) / len(month_logged)
        avg_sleep_m = sum(log_by_date[ds].get("sleep_hours", 7) for ds in month_logged) / len(month_logged)
        bleed_days  = sum(1 for ds in month_logged if "bleeding" in log_by_date[ds].get("symptoms", {}))

        c1, c2, c3, c4 = st.columns(4)
        tiles = [
            (len(month_logged),      "days logged"),
            (f"{avg:.0f}",           "avg score"),
            (f"{avg_mood_m:.1f}/5",  "avg mood"),
            (f"{avg_sleep_m:.1f}h",  "avg sleep"),
        ]
        for col, (val, lbl) in zip([c1, c2, c3, c4], tiles):
            with col:
                st.markdown(f"""<div class="metric-tile">
                    <div class="metric-val">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        if bleed_days:
            st.markdown(
                f'<div class="alert-card" style="margin-top:0.5rem">'
                f'Bleeding was logged on <b>{bleed_days}</b> day{"s" if bleed_days > 1 else ""} this month.</div>',
                unsafe_allow_html=True,
            )