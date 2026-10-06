import random
from curl_cffi import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import altair as alt

st.set_page_config(page_title="Australian PowerBall Simulator", layout="wide")

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
BLUE_BALLS = list(range(1, 36))
POWER_BALLS = list(range(1, 21))
COST_PER_GAME = 1.58  # Standard Powerball entry price per game

LATEST_RESULTS_URL = "https://data.api.thelott.com/sales/vmax/web/data/lotto/latestresults"

TIMES_WON_LABELS = {
    "7+P": "Div 1: 7 Balls + Powerball",
    "7":   "Div 2: 7 Balls",
    "6+P": "Div 3: 6 Balls + Powerball",
    "6":   "Div 4: 6 Balls",
    "5+P": "Div 5: 5 Balls + Powerball",
    "4+P": "Div 6: 4 Balls + Powerball",
    "5":   "Div 7: 5 Balls",
    "3+P": "Div 8: 3 Balls + Powerball",
    "2+P": "Div 9: 2 Balls + Powerball"
}

FALLBACK_PRIZES = {
    "7+P": 20_000_000.00,
    "7":   128_161.72,
    "6+P": 6_026.19,
    "6":   459.55,
    "5+P": 160.45,
    "4+P": 71.58,
    "5":   42.51,
    "3+P": 17.89,
    "2+P": 10.88
}

DIVISION_MAP = {
    1: "7+P",
    2: "7",
    3: "6+P",
    4: "6",
    5: "5+P",
    6: "4+P",
    7: "5",
    8: "3+P",
    9: "2+P"
}

# ==========================================
# VISUAL BALL HELPER FUNCTION
# ==========================================
def render_ball_html(numbers, is_pb=False, matched=False):
    """Generates styled circular lottery ball chips in HTML."""
    if not isinstance(numbers, list):
        numbers = [numbers]
        
    balls_html = ""
    for num in sorted(numbers):
        if matched and is_pb:
            # Matched Powerball (White ball with Gold Ring)
            bg_color = "#ffffff"
            border = "3px solid #ffd700"
            text_color = "#111111"
        elif matched:
            # Matched Standard Ball (Green ball with Gold Ring)
            bg_color = "#38a169"
            border = "3px solid #ffd700"
            text_color = "#ffffff"
        elif is_pb:
            # Unmatched Powerball (White ball)
            bg_color = "#ffffff"
            border = "1px solid #cccccc"
            text_color = "#111111"
        else:
            # Unmatched Standard Ball (Blue ball)
            bg_color = "#3182ce"
            border = "1px solid #2b6cb0"
            text_color = "#ffffff"

        balls_html += f'<div style="display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: 50%; background-color: {bg_color}; color: {text_color}; border: {border}; font-weight: bold; font-size: 15px; margin: 3px; box-shadow: 1px 2px 4px rgba(0,0,0,0.25);">{num}</div>'
    return balls_html

# ==========================================
# DATA FETCHING & COMPOUNDING HELPERS
# ==========================================
@st.cache_data(ttl=1800)
def fetch_live_powerball_data():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.thelott.com",
        "Referer": "https://www.thelott.com/powerball/results",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }

    payload = {
        "CompanyId": "NSWLotteries",
        "MaxDrawCountPerProduct": 1,
        "OptionalProductFilter": ["Powerball"]
    }

    try:
        res = requests.post(
            LATEST_RESULTS_URL,
            json=payload,
            headers=headers,
            impersonate="chrome120",
            timeout=10
        )
        res.raise_for_status()
        data = res.json()

        draw_results = data.get("DrawResults", [])
        if not draw_results:
            return {"prizes": FALLBACK_PRIZES, "live": False, "error": "No DrawResults in response"}

        draw = draw_results[0]
        live_prizes = FALLBACK_PRIZES.copy()

        for div_info in draw.get("Dividends", []):
            div_num = div_info.get("Division")
            payout = div_info.get("BlocPayOut")
            if div_num in DIVISION_MAP and payout is not None:
                live_prizes[DIVISION_MAP[div_num]] = float(payout)

        return {
            "draw_number": draw.get("DrawNumber"),
            "draw_date": draw.get("DrawDate"),
            "winning_numbers": draw.get("PrimaryNumbers", []),
            "powerball": draw.get("SecondaryNumbers", [None])[0],
            "prizes": live_prizes,
            "live": True
        }
    except Exception as e:
        return {
            "prizes": FALLBACK_PRIZES,
            "live": False,
            "error": str(e)
        }

def calculate_compound_growth(weekly_spend, years=30, annual_return=0.07):
    monthly_contribution = weekly_spend * (52 / 12)
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1
    total_months = years * 12

    months = []
    lottery_spent = []
    investment_value = []

    current_inv = 0.0
    current_spent = 0.0

    for m in range(1, total_months + 1):
        current_spent += monthly_contribution
        current_inv = (current_inv + monthly_contribution) * (1 + monthly_rate)

        months.append(m / 12)
        lottery_spent.append(current_spent)
        investment_value.append(current_inv)

    return pd.DataFrame({
        "Years": months,
        "Lottery Outlay": lottery_spent,
        "S&P 500 Value": investment_value
    })

# ==========================================
# APP UI & INPUT CONTROLS
# ==========================================
st.title("Australian PowerBall Simulator")

live_data = fetch_live_powerball_data()
if live_data and live_data.get("live"):
    prize_values = live_data["prizes"]
    st.sidebar.success(f"Connected: Draw #{live_data['draw_number']} Payouts Loaded")
    st.sidebar.markdown(f"**Last Draw Div 1:** ${prize_values['7+P']:,.2f}")
    if live_data.get("winning_numbers"):
        nums = ", ".join(map(str, live_data["winning_numbers"]))
        st.sidebar.markdown(f"**Winning Numbers:** `{nums}` | **PB:** `{live_data['powerball']}`")
else:
    prize_values = FALLBACK_PRIZES
    st.sidebar.warning("Using static fallback prize payouts.")
    if live_data and live_data.get("error"):
        st.sidebar.caption(f"Reason: `{live_data['error']}`")

col_mode, col_inputs = st.columns([1, 2])

with col_mode:
    game_mode = st.radio("Game Mode:", ['QuickPick', 'Marked Entry'])

with col_inputs:
    c1, c2 = st.columns(2)
    tickets = c1.number_input('Tickets (Games per Draw):', min_value=1, value=1)
    games = c2.number_input('Draws to Simulate:', min_value=1, value=10)

user_blues = set()
user_PB = None

if game_mode == 'Marked Entry':
    st.markdown("---")
    cm1, cm2 = st.columns(2)
    user_blues = set(cm1.multiselect('Select 7 Standard Numbers:', BLUE_BALLS, max_selections=7))
    user_PB = cm2.selectbox('Select Powerball:', POWER_BALLS)

# ==========================================
# SIMULATION ENGINE
# ==========================================
if st.button('Play Games', type='primary'):
    if game_mode == 'Marked Entry' and len(user_blues) != 7:
        st.error("Please select exactly 7 Standard balls before proceeding.")
        st.stop()

    total_spent = (games * tickets) * COST_PER_GAME
    earnings = 0.0
    times_won = {key: 0 for key in TIMES_WON_LABELS}
    standard_ball_frequency = {ball: 0 for ball in BLUE_BALLS}
    power_ball_frequency = {ball: 0 for ball in POWER_BALLS}

    preselected_blues = user_blues
    preselected_pb = user_PB

    history_draws = []

    for draw_idx in range(games):
        winning_blues = set(random.sample(BLUE_BALLS, 7))
        winning_PB = random.choice(POWER_BALLS)

        for wb in winning_blues:
            standard_ball_frequency[wb] += 1
        power_ball_frequency[winning_PB] += 1

        draw_tickets = []

        for _ in range(tickets):
            if game_mode == 'QuickPick':
                my_blues = set(random.sample(BLUE_BALLS, 7))
                my_PB = random.choice(POWER_BALLS)
            else:
                my_blues = preselected_blues
                my_PB = preselected_pb

            blue_matches = my_blues.intersection(winning_blues)
            power_matches = (my_PB == winning_PB)

            div_key = None
            if len(blue_matches) == 7:
                div_key = "7+P" if power_matches else "7"
            elif len(blue_matches) == 6:
                div_key = "6+P" if power_matches else "6"
            elif len(blue_matches) == 5:
                div_key = "5+P" if power_matches else "5"
            elif len(blue_matches) == 4 and power_matches:
                div_key = "4+P"
            elif len(blue_matches) == 3 and power_matches:
                div_key = "3+P"
            elif len(blue_matches) == 2 and power_matches:
                div_key = "2+P"

            payout = 0.0
            if div_key:
                times_won[div_key] += 1
                payout = prize_values[div_key]
                earnings += payout

            if draw_idx < 10:
                draw_tickets.append({
                    "my_blues": my_blues,
                    "my_pb": my_PB,
                    "matched_blues": blue_matches,
                    "matched_pb": power_matches,
                    "div": div_key,
                    "payout": payout
                })

        if draw_idx < 10:
            history_draws.append({
                "draw_num": draw_idx + 1,
                "winning_blues": winning_blues,
                "winning_pb": winning_PB,
                "tickets": draw_tickets
            })

    # ==========================================
    # DRAW RESULTS & TICKET VERIFICATION DISPLAY
    # ==========================================
    st.subheader("Draw Results & Ticket Verification")

    def display_single_draw(d):
        st.markdown(f"#### Draw #{d['draw_num']}")
        
        winning_balls_html = render_ball_html(list(d["winning_blues"]))
        pb_html = render_ball_html([d["winning_pb"]], is_pb=True)
        
        st.markdown(
            f'<div style="background-color: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 15px;">'
            f'<div style="font-weight: bold; margin-bottom: 6px;">Winning Numbers Drawn:</div>'
            f'<div style="display: flex; align-items: center; flex-wrap: wrap;">'
            f'{winning_balls_html}'
            f'<span style="font-size: 20px; font-weight: bold; margin: 0 10px; color: #ffffff;">+</span>'
            f'{pb_html}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        for t_idx, t in enumerate(d["tickets"][:10]):
            matched_b = t["matched_blues"]
            unmatched_b = t["my_blues"] - matched_b

            t_matched_html = render_ball_html(list(matched_b), matched=True) if matched_b else ""
            t_unmatched_html = render_ball_html(list(unmatched_b)) if unmatched_b else ""
            t_pb_html = render_ball_html([t["my_pb"]], is_pb=True, matched=t["matched_pb"])

            status_label = f"**{TIMES_WON_LABELS[t['div']]}** (Won ${t['payout']:,.2f})" if t["div"] else "No Win ($0.00)"

            border_color = "#38a169" if t["div"] else "#718096"
            st.markdown(
                f'<div style="border-left: 3px solid {border_color}; padding-left: 10px; margin: 8px 0;">'
                f'<span style="font-weight: 500;">Ticket #{t_idx + 1} — Result: {status_label}</span>'
                f'<div style="display: flex; align-items: center; flex-wrap: wrap; margin-top: 4px;">'
                f'{t_matched_html}'
                f'{t_unmatched_html}'
                f'<span style="font-size: 16px; margin: 0 8px; color: #ffffff;">+</span>'
                f'{t_pb_html}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        if len(d["tickets"]) > 10:
            st.caption(f"... and {len(d['tickets']) - 10} more tickets in this draw.")

    if history_draws:
        display_single_draw(history_draws[0])

    if len(history_draws) > 1:
        with st.expander(f"View Remaining Draws ({len(history_draws) - 1} more)", expanded=False):
            for remaining_draw in history_draws[1:]:
                display_single_draw(remaining_draw)
                st.markdown("---")

    st.markdown("---")

    # ==========================================
    # METRICS & VISUALIZATIONS
    # ==========================================
    net_profit = earnings - total_spent
    st.markdown("### Simulation Summary")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Spent", f"${total_spent:,.2f}")
    m2.metric("Total Earnings", f"${earnings:,.2f}")
    m3.metric("Net Profit / Loss", f"${net_profit:,.2f}", delta=f"{net_profit:,.2f}")
    m4.metric("Return on Investment", f"{(earnings / total_spent) * 100:.2f}%" if total_spent > 0 else "0.00%")

    table_data = [
        {
            "Winning Combination": TIMES_WON_LABELS[key],
            "Dividend Payout": f"${prize_values[key]:,.2f}",
            "Count": times_won[key],
            "Total Payout": f"${times_won[key] * prize_values[key]:,.2f}"
        }
        for key in TIMES_WON_LABELS
    ]
    df_table = pd.DataFrame(table_data)

    st.subheader("Winnings Breakdown")
    st.dataframe(df_table, use_container_width=True)

    st.download_button(
        "Download Results as CSV",
        df_table.to_csv(index=False),
        "results.csv",
        "text/csv"
    )

    tab_hist, tab_freq, tab_sorted, tab_radial, tab_opportunity = st.tabs([
        "Winnings Histogram",
        "Frequency Charts",
        "Sorted Frequency",
        "Radial Charts",
        "Opportunity Cost"
    ])

    with tab_hist:
        st.subheader("Wins Count by Division")
        st.bar_chart(df_table.set_index("Winning Combination")["Count"])

    with tab_freq:
        df_standard = pd.DataFrame(list(standard_ball_frequency.items()), columns=["Ball", "Count"])
        df_power = pd.DataFrame(list(power_ball_frequency.items()), columns=["Ball", "Count"])

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Standard Ball Frequency (1-35)")
            st.bar_chart(df_standard.set_index("Ball")["Count"])
        with col2:
            st.subheader("PowerBall Frequency (1-20)")
            st.bar_chart(df_power.set_index("Ball")["Count"])

    with tab_sorted:
        st.subheader("Sorted Ball Frequency (Most to Least Frequent)")

        df_standard_sorted = pd.DataFrame(list(standard_ball_frequency.items()), columns=["Ball", "Count"]).sort_values(by="Count", ascending=False)
        df_power_sorted = pd.DataFrame(list(power_ball_frequency.items()), columns=["Ball", "Count"]).sort_values(by="Count", ascending=False)

        df_standard_sorted['Ball'] = df_standard_sorted['Ball'].astype(str)
        df_power_sorted['Ball'] = df_power_sorted['Ball'].astype(str)

        col1, col2 = st.columns(2)
        with col1:
            chart_standard = alt.Chart(df_standard_sorted).mark_bar().encode(
                x=alt.X('Ball:N', sort='-y', title="Standard Ball #"),
                y=alt.Y('Count:Q', axis=alt.Axis(format='d'), title="Frequency")
            ).properties(title="Standard Balls")
            st.altair_chart(chart_standard, use_container_width=True)

        with col2:
            chart_power = alt.Chart(df_power_sorted).mark_bar().encode(
                x=alt.X('Ball:N', sort='-y', title="Powerball #"),
                y=alt.Y('Count:Q', axis=alt.Axis(format='d'), title="Frequency")
            ).properties(title="Powerballs")
            st.altair_chart(chart_power, use_container_width=True)

    with tab_radial:
        st.subheader("Radial Distribution")

        cat_std = [str(i) for i in range(1, 36)]
        val_std = [standard_ball_frequency[i] for i in range(1, 36)]
        fig_standard = go.Figure(go.Scatterpolar(
            r=val_std + [val_std[0]],
            theta=cat_std + [cat_std[0]],
            fill='toself',
            name='Standard Balls'
        ))
        fig_standard.update_layout(
            polar=dict(angularaxis=dict(direction='clockwise', rotation=90)),
            showlegend=False,
            title="Standard Balls (1-35)"
        )

        cat_pow = [str(i) for i in range(1, 21)]
        val_pow = [power_ball_frequency[i] for i in range(1, 21)]
        fig_power = go.Figure(go.Scatterpolar(
            r=val_pow + [val_pow[0]],
            theta=cat_pow + [cat_pow[0]],
            fill='toself',
            name='Powerball'
        ))
        fig_power.update_layout(
            polar=dict(angularaxis=dict(direction='clockwise', rotation=90)),
            showlegend=False,
            title="Powerballs (1-20)"
        )

        col_r1, col_r2 = st.columns(2)
        col_r1.plotly_chart(fig_standard, use_container_width=True)
        col_r2.plotly_chart(fig_power, use_container_width=True)

    with tab_opportunity:
        st.subheader("Opportunity Cost: Playing vs. Investing")
        st.markdown(
            "What happens if that exact ticket outlay is redirected to a low-cost "
            "S&P 500 / broad-market index fund compounding over time?"
        )

        col_opt1, col_opt2 = st.columns(2)
        time_horizon = col_opt1.slider("Timeline (Years):", min_value=5, max_value=50, value=30, step=5)
        assumed_return = col_opt2.slider("Assumed Annual Return (%):", min_value=3.0, max_value=12.0, value=7.0, step=0.5) / 100

        weekly_spend = tickets * COST_PER_GAME
        st.info(f"**Simulated Habit Spend:** ${weekly_spend:,.2f} per weekly draw (~${weekly_spend * (52 / 12):,.2f} / month)")

        df_growth = calculate_compound_growth(weekly_spend, years=time_horizon, annual_return=assumed_return)

        final_spent = df_growth["Lottery Outlay"].iloc[-1]
        final_invested = df_growth["S&P 500 Value"].iloc[-1]
        wealth_lost = final_invested - final_spent

        mo1, mo2, mo3 = st.columns(3)
        mo1.metric("Total Spent on Lottery", f"${final_spent:,.2f}")
        mo2.metric(f"Index Fund Value ({time_horizon} Yrs)", f"${final_invested:,.2f}")
        mo3.metric("Wealth Gap (Missed Compound Growth)", f"${wealth_lost:,.2f}", delta=f"-${wealth_lost:,.2f}")

        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=df_growth["Years"],
            y=df_growth["S&P 500 Value"],
            mode='lines',
            name='S&P 500 Compound Growth',
            line=dict(color='#2ca02c', width=3)
        ))
        fig_growth.add_trace(go.Scatter(
            x=df_growth["Years"],
            y=df_growth["Lottery Outlay"],
            mode='lines',
            name='Cumulative Lottery Outlay',
            line=dict(color='#d62728', width=2, dash='dash')
        ))
        fig_growth.update_layout(
            title=f"Cumulative Lottery Outlay vs. Compound Growth over {time_horizon} Years",
            xaxis_title="Years",
            yaxis_title="Amount ($ AUD)",
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig_growth, use_container_width=True)
