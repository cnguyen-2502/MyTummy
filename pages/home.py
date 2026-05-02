import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import streamlit as st
from datetime import date
from utils.helpers import (get_week_of_pregnancy, get_trimester, trimester_class,
                           compute_daily_score, score_color, score_label,
                           FETAL_MILESTONES, TRIMESTER_INFO)

def render(dm):
    name = st.session_state.get("name", "Mama")
    due_date = st.session_state.get("due_date")

    st.markdown(f'<div class="page-header">Welcome back, {name}</div>', unsafe_allow_html=True)

    if not due_date:
        st.info("Set your due date to get started.")
        return

    week, days = get_week_of_pregnancy(due_date)
    trimester = get_trimester(week)
    tc = trimester_class(week)

    days_until_due = (date.fromisoformat(due_date) - date.today()).days

    # -- Top stats row --
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-tile">
            <div class="metric-val">Week {week}</div>
            <div class="metric-lbl">of pregnancy</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-tile">
            <div class="metric-val">{days_until_due}</div>
            <div class="metric-lbl">days until due date</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-tile">
            <div class="metric-val"><span class="trimester-badge {tc}">{trimester}</span></div>
            <div class="metric-lbl">&nbsp;</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        logs = dm.get_daily_logs()
        today_log = dm.get_daily_log_for(str(date.today()))
        if today_log:
            score = compute_daily_score(today_log)
            color = score_color(score)
            label = score_label(score)
            st.markdown(f"""<div class="metric-tile">
                <div class="metric-val" style="color:{color}">{score}</div>
                <div class="metric-lbl">Today's score · {label}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="metric-tile">
                <div class="metric-val" style="font-size:1rem;color:var(--text-muted)">—</div>
                <div class="metric-lbl">Log today to see score</div>
            </div>""", unsafe_allow_html=True)

    # -- Log today button --
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("Log today's wellbeing", use_container_width=True):
            st.session_state["nav_target"] = "Daily Log"
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    with left:
        # Trimester info card
        info = TRIMESTER_INFO[trimester]
        st.markdown(f"""
        <div class="card">
            <div class="card-title">{trimester} — {info['weeks']}</div>
            <p style="color:var(--text-muted);font-size:0.88rem;margin-bottom:0.75rem">{info['focus']}</p>
            <b style="font-size:0.85rem">Common symptoms:</b>
            <div style="margin-top:0.4rem;display:flex;flex-wrap:wrap;gap:0.4rem">
                {"".join(f'<span class="stat-pill">{s}</span>' for s in info["common_symptoms"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recent wellness scores
        st.markdown('<div class="card-title">Recent wellness scores</div>', unsafe_allow_html=True)
        recent = sorted(dm.get_daily_logs(), key=lambda x: x.get("date", ""), reverse=True)[:7]
        if recent:
            import plotly.graph_objects as go
            dates = [l["date"] for l in reversed(recent)]
            scores = [compute_daily_score(l) for l in reversed(recent)]
            fig = go.Figure(go.Scatter(
                x=dates, y=scores, mode="lines+markers",
                line=dict(color="#E0737D", width=2.5),
                marker=dict(size=7, color="#9E6B7A"),
                fill="tozeroy", fillcolor="rgba(224,115,125,0.1)"
            ))
            fig.update_layout(
                height=200, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(
                    range=[0, 100],
                    gridcolor="#EDCFC8",
                    tickfont=dict(size=11, color="#1a1a1a"),
                    tickcolor="#1a1a1a",
                ),
                xaxis=dict(
                    gridcolor="rgba(0,0,0,0)",
                    tickfont=dict(size=11, color="#1a1a1a"),
                    tickcolor="#1a1a1a",
                ),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Start logging daily to see your wellness trends.")

    with right:
        # Upcoming milestone
        upcoming = [(w, m) for w, m in FETAL_MILESTONES.items() if w >= week]
        if upcoming:
            next_week, next_milestone = upcoming[0]
            weeks_away = next_week - week
            st.markdown(f"""
            <div class="card">
                <div class="card-title">Next Milestone</div>
                <div class="milestone">{next_milestone}</div>
                <div style="font-size:0.8rem;color:var(--text-muted);margin-top:0.5rem">
                    Week {next_week} · in {weeks_away} week{'s' if weeks_away != 1 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Alerts
        if today_log:
            alerts = []
            symptoms = today_log.get("symptoms", {})
            if "bleeding" in symptoms:
                alerts.append(("Bleeding was logged today. Please contact your doctor.", "danger"))
            if "headache" in symptoms and symptoms.get("headache", 0) >= 3:
                alerts.append(("Severe headache noted. Monitor blood pressure and contact your provider if persistent.", "warning"))
            pain = today_log.get("pain", 0)
            if pain >= 7:
                alerts.append((f"High pain level ({pain}/10) logged. If severe or sudden, seek medical attention.", "warning"))

            for msg, level in alerts:
                css_class = "alert-card" if level == "danger" else "warning-card"
                st.markdown(f'<div class="{css_class}">{msg}</div>', unsafe_allow_html=True)

        # Nutrition reminder
        tri_nutrition = TRIMESTER_INFO[trimester]["nutrition"]
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Nutrition Focus</div>
            {"".join(f'<div style="font-size:0.85rem;padding:0.2rem 0;border-bottom:1px solid var(--border)">+ {n}</div>' for n in tri_nutrition)}
        </div>
        """, unsafe_allow_html=True)