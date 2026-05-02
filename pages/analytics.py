import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.helpers import compute_daily_score

COLORS = dict(rose="#E8707B", mauve="#9E6B7A", sage="#8BAF8B",
              blush="#F4AFAF", soft="#D4EAD4", warn="#E8A030")

TEXT     = "#3D2B35"
TEXT_MID = "#6B4A57"
GRID     = "#EDCFC8"

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=TEXT),
    title_font=dict(size=14, color=COLORS["mauve"]),
    legend=dict(orientation="h", y=-0.28, font=dict(size=11, color=TEXT_MID)),
    margin=dict(l=56, r=16, t=44, b=60),
)


def _style_axes(fig, x_title="", y_title="", y2_title=None):
    """
    Uses title_text + title_font (flat form) which Plotly reliably applies
    even on transparent-background charts.
    """
    def _ax(label):
        return dict(
            title_text=label,
            title_font=dict(size=12, color=TEXT),
            tickfont=dict(size=11, color=TEXT),
            gridcolor=GRID,
            zeroline=False,
            linecolor=GRID,
            linewidth=1,
            showline=True,
        )
    fig.update_xaxes(**_ax(x_title))
    fig.update_yaxes(**_ax(y_title))
    if y2_title is not None:
        fig.update_yaxes(secondary_y=True, **_ax(y2_title))


def _vitamins_taken(val) -> int:
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, dict):
        return sum(1 for v in val.values() if v)
    return 0


def _trendline(x_vals, y_vals):
    mask = ~(np.isnan(x_vals) | np.isnan(y_vals))
    if mask.sum() < 2:
        return [], []
    m, b = np.polyfit(x_vals[mask], y_vals[mask], 1)
    x0, x1 = float(x_vals[mask].min()), float(x_vals[mask].max())
    return [x0, x1], [m * x0 + b, m * x1 + b]


def render(dm):
    st.markdown('<div class="page-header">Analytics & Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Understand your pregnancy wellness trends</div>', unsafe_allow_html=True)

    daily_logs  = dm.get_daily_logs()
    weekly_logs = dm.get_weekly_logs()

    if len(daily_logs) < 2:
        st.info("Log at least 2 days of data to see your analytics. Head to Daily Log to get started.")
        return

    rows = []
    for log in sorted(daily_logs, key=lambda x: x.get("date", "")):
        score    = compute_daily_score(log)
        symptoms = log.get("symptoms", {})
        rows.append({
            "date":          log["date"],
            "score":         score,
            "energy":        log.get("energy", 3),
            "mood":          log.get("mood", 3),
            "sleep_hours":   log.get("sleep_hours", 7),
            "sleep_quality": log.get("sleep_quality", 3),
            "pain":          log.get("pain", 0),
            "vitamins":      _vitamins_taken(log.get("vitamins", {})),
            "hydration":     log.get("hydration", 1),
            "nausea_sev":    symptoms.get("nausea", 0),
            "has_bleeding":  int("bleeding" in symptoms),
            "has_headache":  int("headache" in symptoms),
            "iron_rich":     int(log.get("iron_rich", False)),
            "movement":      int(log.get("movement", False)),
            "ate_well":      int(log.get("ate_well", False)),
        })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])

    tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Weight & Vitals", "Correlations", "Insights"])

    # ════════════════════════════════════════
    # TAB 1 — Trends
    # ════════════════════════════════════════
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["score"],
            mode="lines+markers",
            line=dict(color=COLORS["rose"], width=2.5),
            marker=dict(size=7, color=COLORS["mauve"], line=dict(color="#fff", width=1.5)),
            fill="tozeroy", fillcolor="rgba(232,112,123,0.08)",
            name="Wellness Score",
        ))
        fig.update_layout(**LAYOUT, title="Daily Wellness Score", height=290,
                          yaxis=dict(range=[0, 100]))
        _style_axes(fig, x_title="", y_title="Score")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2 = st.columns(2)
        with c1:
            fig2 = make_subplots(specs=[[{"secondary_y": True}]])
            fig2.add_trace(go.Bar(x=df["date"], y=df["sleep_hours"], name="Sleep hrs",
                                  marker_color=COLORS["blush"], marker_line_width=0), secondary_y=False)
            fig2.add_trace(go.Scatter(x=df["date"], y=df["energy"], mode="lines+markers",
                                      name="Energy", line=dict(color=COLORS["rose"], width=2),
                                      marker=dict(size=5)), secondary_y=True)
            fig2.update_layout(**LAYOUT, title="Sleep vs Energy", height=270)
            _style_axes(fig2, x_title="", y_title="Sleep hrs", y2_title="Energy (1–5)")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with c2:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["date"], y=df["mood"], mode="lines+markers",
                                      name="Mood", line=dict(color=COLORS["mauve"], width=2),
                                      marker=dict(size=5)))
            fig3.add_trace(go.Scatter(x=df["date"], y=df["pain"], mode="lines+markers",
                                      name="Pain", line=dict(color=COLORS["warn"], width=2, dash="dot"),
                                      marker=dict(size=5)))
            fig3.update_layout(**LAYOUT, title="Mood & Pain", height=270)
            _style_axes(fig3, x_title="", y_title="Rating")
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        sym_counts = {}
        for log in daily_logs:
            for sym in log.get("symptoms", {}):
                sym_counts[sym] = sym_counts.get(sym, 0) + 1
        if sym_counts:
            fig4 = go.Figure(go.Bar(
                x=list(sym_counts.keys()), y=list(sym_counts.values()),
                marker_color=[COLORS["rose"] if s == "bleeding" else COLORS["blush"]
                              for s in sym_counts],
                marker_line_width=0,
            ))
            fig4.update_layout(**LAYOUT, title="Symptom Frequency", height=240)
            _style_axes(fig4, x_title="", y_title="Days logged")
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    # ════════════════════════════════════════
    # TAB 2 — Weight & Vitals
    # ════════════════════════════════════════
    with tab2:
        weekly_logs_sorted = sorted(weekly_logs, key=lambda x: x.get("week", 0))
        if weekly_logs_sorted:
            w_df = pd.DataFrame(weekly_logs_sorted)

            if "weight" in w_df.columns:
                fig_w = go.Figure()
                fig_w.add_trace(go.Scatter(
                    x=w_df["week"], y=w_df["weight"], mode="lines+markers", name="Weight (lbs)",
                    line=dict(color=COLORS["rose"], width=2.5),
                    marker=dict(size=8, color=COLORS["mauve"], line=dict(color="#fff", width=1.5)),
                ))
                fig_w.update_layout(**LAYOUT, title="Weight over Pregnancy Weeks", height=290)
                _style_axes(fig_w, x_title="Week", y_title="Weight (lbs)")
                st.plotly_chart(fig_w, use_container_width=True, config={"displayModeBar": False})

            if "bp_sys" in w_df.columns:
                fig_bp = go.Figure()
                fig_bp.add_trace(go.Scatter(x=w_df["week"], y=w_df["bp_sys"], mode="lines+markers",
                                            name="Systolic", line=dict(color=COLORS["rose"], width=2),
                                            marker=dict(size=6)))
                fig_bp.add_trace(go.Scatter(x=w_df["week"], y=w_df["bp_dia"], mode="lines+markers",
                                            name="Diastolic", line=dict(color=COLORS["blush"], width=2),
                                            marker=dict(size=6)))
                fig_bp.add_hline(y=140, line_dash="dash", line_color=COLORS["warn"],
                                 annotation_text="High systolic threshold",
                                 annotation_font=dict(color=COLORS["warn"], size=11))
                fig_bp.update_layout(**LAYOUT, title="Blood Pressure Trend", height=270)
                _style_axes(fig_bp, x_title="Week", y_title="mmHg")
                st.plotly_chart(fig_bp, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Complete weekly check-ins to see weight and vitals trends.")

    # ════════════════════════════════════════
    # TAB 3 — Correlations
    # ════════════════════════════════════════
    with tab3:
        st.markdown('<div class="card-title">Correlation Explorer</div>', unsafe_allow_html=True)
        st.caption("Explore relationships between wellness factors. Suggestive only — not diagnostic.")

        col_options = {
            "Wellness Score":  "score",
            "Energy":          "energy",
            "Mood":            "mood",
            "Sleep hours":     "sleep_hours",
            "Sleep quality":   "sleep_quality",
            "Pain level":      "pain",
            "Nausea severity": "nausea_sev",
            "Hydration":       "hydration",
        }

        if len(df) >= 5:
            c1, c2 = st.columns(2)
            with c1:
                x_label = st.selectbox("X axis", list(col_options.keys()), index=2)
            with c2:
                y_label = st.selectbox("Y axis", list(col_options.keys()), index=0)

            x_col  = col_options[x_label]
            y_col  = col_options[y_label]
            x_vals = df[x_col].to_numpy(dtype=float)
            y_vals = df[y_col].to_numpy(dtype=float)
            x_line, y_line = _trendline(x_vals, y_vals)

            fig_corr = go.Figure()
            fig_corr.add_trace(go.Scatter(
                x=x_vals, y=y_vals, mode="markers",
                marker=dict(color=COLORS["rose"], size=9, opacity=0.8,
                            line=dict(color=COLORS["mauve"], width=1.2)),
                name="Data points",
            ))
            if x_line:
                fig_corr.add_trace(go.Scatter(
                    x=x_line, y=y_line, mode="lines",
                    line=dict(color=COLORS["mauve"], width=2, dash="dash"),
                    name="Linear trend",
                ))
            fig_corr.update_layout(**LAYOUT, title=f"{x_label} vs {y_label}", height=330)
            _style_axes(fig_corr, x_title=x_label, y_title=y_label)
            st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})

            corr_cols   = list(col_options.values())
            corr_matrix = df[corr_cols].corr().round(2)
            fig_heat    = go.Figure(go.Heatmap(
                z=corr_matrix.values,
                x=list(col_options.keys()),
                y=list(col_options.keys()),
                colorscale=[[0, "#f0e0e5"], [0.5, "#E8707B"], [1, "#9E6B7A"]],
                zmin=-1, zmax=1,
                text=corr_matrix.values,
                texttemplate="%{text:.2f}",
                textfont=dict(size=11, color=TEXT),
                showscale=True,
                colorbar=dict(title="r",
                              tickfont=dict(size=11, color=TEXT),
                              title_font=dict(size=12, color=TEXT)),
            ))
            heat_layout = {**LAYOUT, "margin": dict(l=140, r=16, t=44, b=100)}
            fig_heat.update_layout(**heat_layout, title="Correlation Matrix", height=440)
            # Heatmap axes need tickangle and autorange handled separately
            fig_heat.update_xaxes(
                tickangle=-35,
                tickfont=dict(size=10, color=TEXT),
                title=dict(font=dict(size=12, color=TEXT)),
                gridcolor=GRID, linecolor=GRID, showline=True,
            )
            fig_heat.update_yaxes(
                autorange="reversed",
                tickfont=dict(size=10, color=TEXT),
                title=dict(font=dict(size=12, color=TEXT)),
                gridcolor=GRID, linecolor=GRID, showline=True,
            )
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Need at least 5 days of logs to generate correlation analysis.")

    # ════════════════════════════════════════
    # TAB 4 — Insights
    # ════════════════════════════════════════
    with tab4:
        st.markdown('<div class="card-title">Personalized Insights</div>', unsafe_allow_html=True)
        st.caption("Based on your logged data — suggestive only, not medical advice.")
        insights = generate_insights(df, weekly_logs)
        if insights:
            for insight in insights:
                msg   = insight["msg"]
                level = insight.get("level", "info")
                if level == "alert":
                    st.markdown(f'<div class="alert-card">{msg}</div>', unsafe_allow_html=True)
                elif level == "warning":
                    st.markdown(f'<div class="warning-card">{msg}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="insight-box">{msg}</div>', unsafe_allow_html=True)
        else:
            st.info("Log more data to generate personalized insights.")


# ════════════════════════════════════════
# Insight generation
# ════════════════════════════════════════
def generate_insights(df, weekly_logs):
    insights = []
    n = len(df)
    if n < 3:
        return insights

    avg_score     = df["score"].mean()
    avg_energy    = df["energy"].mean()
    avg_mood      = df["mood"].mean()
    avg_pain      = df["pain"].mean()
    avg_sleep_h   = df["sleep_hours"].mean()
    avg_sleep_q   = df["sleep_quality"].mean()
    avg_nausea    = df["nausea_sev"].mean()
    avg_hydration = df["hydration"].mean()

    if n >= 7:
        recent  = df["score"].iloc[-3:].mean()
        earlier = df["score"].iloc[:3].mean()
        if recent - earlier >= 10:
            insights.append({"msg": "Your overall wellness score has been trending upward — a positive sign. Keep doing what you're doing.", "level": "info"})
        elif earlier - recent >= 10:
            insights.append({"msg": "Your overall wellness score has dipped over the past few days. Consider whether sleep, stress, or nutrition may be contributing.", "level": "warning"})

    corr_se = df["sleep_hours"].corr(df["energy"])
    if abs(corr_se) > 0.4:
        direction = "more sleep tends to boost" if corr_se > 0 else "more sleep does not appear to be improving"
        insights.append({"msg": f"Your data suggests that {direction} your energy levels. The recommended amount during pregnancy is 7–9 hours per night.", "level": "info"})

    if avg_sleep_h < 6:
        insights.append({"msg": f"You are averaging {avg_sleep_h:.1f} hours of sleep per night, which is below the recommended range. Consistent rest is especially important during pregnancy — try to prioritise sleep where possible.", "level": "warning"})
    elif avg_sleep_h >= 9.5:
        insights.append({"msg": f"You are averaging {avg_sleep_h:.1f} hours of sleep, which is on the higher end. Excessive sleep can sometimes indicate fatigue or low mood — worth mentioning to your provider if it persists.", "level": "info"})

    if avg_sleep_q <= 2:
        insights.append({"msg": "Sleep quality has consistently been rated low. Poor sleep quality can compound fatigue and mood changes. A pregnancy pillow, reducing screen time before bed, or discussing this with your midwife may help.", "level": "warning"})

    if avg_energy < 2.5:
        insights.append({"msg": "Energy levels have been consistently low across your logged days. This can be normal in the first trimester or later in pregnancy, but persistent fatigue is worth discussing with your provider, particularly to rule out anaemia.", "level": "warning"})
    elif avg_energy >= 4:
        insights.append({"msg": "Your energy levels have been good overall. This is a great time to stay active with gentle exercise if you feel up to it.", "level": "info"})

    if avg_mood < 2.5:
        insights.append({"msg": "Mood has been rated low on many logged days. Emotional wellbeing is an important part of prenatal health. If low mood is persistent, please speak with your midwife or GP — support is available.", "level": "warning"})

    if n >= 5 and df["mood"].std() > 1.2:
        insights.append({"msg": "Mood has been quite variable day to day. Hormonal changes during pregnancy can contribute to mood swings, but if swings feel intense or unmanageable, it's worth raising with your provider.", "level": "info"})

    if df["mood"].corr(df["pain"]) < -0.35:
        insights.append({"msg": "There is a pattern in your data linking lower mood with higher pain levels. Stress and discomfort can reinforce each other. Prenatal yoga, mindful breathing, or a short walk may help on difficult days.", "level": "info"})

    if avg_pain >= 5:
        insights.append({"msg": f"Pain has been averaging {avg_pain:.1f} out of 10 across logged days — a level that warrants attention. Please discuss persistent pain with your healthcare provider.", "level": "alert"})
    elif avg_pain >= 3:
        insights.append({"msg": f"Pain has been moderate on average ({avg_pain:.1f}/10). If this is concentrated in the pelvis or lower back, pelvic girdle pain is common in pregnancy and physiotherapy can be very effective.", "level": "warning"})

    bleeding_days = df["has_bleeding"].sum()
    if bleeding_days > 0:
        insights.append({"msg": f"Bleeding has been logged on {bleeding_days} day(s). Any vaginal bleeding during pregnancy should be assessed by your healthcare provider, even if it has resolved.", "level": "alert"})

    headache_days = df["has_headache"].sum()
    if headache_days >= 3:
        insights.append({"msg": f"Headaches have been logged on {headache_days} days. Frequent headaches in pregnancy can have several causes, including dehydration, blood pressure changes, or tension. Please mention this pattern to your provider.", "level": "warning"})

    if avg_nausea > 3.5:
        insights.append({"msg": "Nausea severity has been high. Hyperemesis gravidarum (severe pregnancy sickness) is a medical condition that requires treatment — please contact your provider if you are struggling to keep food or fluids down.", "level": "alert"})
    elif avg_nausea > 2 and n >= 5:
        insights.append({"msg": "Nausea has been consistently present in your logs. Eating small, frequent meals, avoiding strong smells, and staying hydrated can help. If nausea is severe or preventing you from eating, speak with your provider — there are safe treatments available.", "level": "info"})

    vitamin_pct = df["vitamins"].mean() * 100
    if vitamin_pct < 50:
        insights.append({"msg": f"Prenatal vitamins were taken on only {vitamin_pct:.0f}% of logged days. Folic acid and other key nutrients are important throughout pregnancy — try to take them at the same time each day to build the habit.", "level": "warning"})
    elif vitamin_pct < 80:
        insights.append({"msg": f"Prenatal vitamins were taken on {vitamin_pct:.0f}% of logged days. Consistent daily intake helps ensure you and your baby are getting adequate folic acid, iron, and vitamin D.", "level": "info"})

    if avg_hydration < 1.5:
        insights.append({"msg": "Hydration has been low across many logged days. Staying well hydrated helps prevent headaches, constipation, and urinary infections — all more common in pregnancy. Aim for 8–10 glasses of water daily.", "level": "warning"})

    if "iron_rich" in df.columns and df["iron_rich"].mean() < 0.4 and avg_energy < 3:
        insights.append({"msg": "Low energy combined with low intake of iron-rich foods is a pattern worth noting. Iron-deficiency anaemia is common in pregnancy. Consider including more spinach, lentils, lean red meat, and fortified cereals in your diet, and ask your provider about your iron levels at your next appointment.", "level": "warning"})

    if "movement" in df.columns and n >= 5 and df["movement"].mean() * 100 < 30:
        movement_pct = df["movement"].mean() * 100
        insights.append({"msg": f"Movement or light exercise has been logged on only {movement_pct:.0f}% of days. Gentle activity such as walking, swimming, or prenatal yoga can improve mood, energy, and sleep quality during pregnancy.", "level": "info"})

    if "ate_well" in df.columns and n >= 5 and df["ate_well"].mean() * 100 < 50:
        ate_pct = df["ate_well"].mean() * 100
        insights.append({"msg": f"Regular meals were logged on only {ate_pct:.0f}% of days. Eating regularly helps stabilise blood sugar, reduce nausea, and support your baby's growth. Even small, frequent snacks count if larger meals feel difficult.", "level": "info"})

    high_bp_weeks = [str(w.get("week", "?")) for w in weekly_logs
                     if w.get("bp_sys", 0) >= 140 or w.get("bp_dia", 0) >= 90]
    if high_bp_weeks:
        insights.append({"msg": f"Blood pressure readings above the normal threshold were recorded in week(s) {', '.join(high_bp_weeks)}. High blood pressure in pregnancy can be a sign of preeclampsia. Please follow up with your provider promptly.", "level": "alert"})

    if avg_score >= 75 and n >= 5:
        insights.append({"msg": f"Your average wellness score over the logged period is {avg_score:.0f} out of 100 — a strong result. Your consistency with logging suggests you are actively engaged in your pregnancy health, which is a great sign.", "level": "info"})

    return insights