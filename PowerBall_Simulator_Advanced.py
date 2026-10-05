import random
import requests
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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Division labels according to official Australian Powerball rules
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
# DATA FETCHING & COMPOUNDING HELPERS
# ==========================================
@st.cache_data(ttl=1800)
def fetch_live_powerball_data():
    """Fetches the latest draw dividend payouts and winning numbers from The Lott API."""
    payload = {
        "CompanyId": "NSWLotteries",
        "MaxDrawCount": 1,
        "OptionalProductFilter": ["Powerball"]
    }
    try:
        res = requests.post(LATEST_RESULTS_URL, json=payload, headers=HEADERS, timeout=8)
        res.raise_for_status()
        data = res.json()

        draw_results = data.get("DrawResults", [])
        if not draw_results:
            return None

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
    """Calculates cumulative lottery cost vs. compound index fund growth with monthly deposits."""
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

# Retrieve live dividend figures
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

    for _ in range(games):
        winning_blues = set(random.sample(BLUE_BALLS, 7))
        winning_PB = random.choice(POWER_BALLS)

        for wb in winning_blues:
            standard_ball_frequency[wb] += 1
        power_ball_frequency[winning_PB] += 1

        for _ in range(tickets):
            if game_mode == 'QuickPick':
                my_blues = set(random.sample(BLUE_BALLS, 7))
                my_PB = random.choice(POWER_BALLS)
            else:
                my_blues = preselected_blues
                my_PB = preselected_pb

            blue_matches = len(my_blues.intersection(winning_blues))
            power_matches = (my_PB == winning_PB)

            # Australian Powerball Division Rules
            div_key = None
            if blue_matches == 7:
                div_key = "7+P" if power_matches else "7"
            elif blue_matches == 6:
                div_key = "6+P" if power_matches else "6"
            elif blue_matches == 5:
                div_key = "5+P" if power_matches else "5"
            elif blue_matches == 4 and power_matches:
                div_key = "4+P"
            elif blue_matches == 3 and power_matches:
                div_key = "3+P"
            elif blue_matches == 2 and power_matches:
                div_key = "2+P"

            if div_key:
                times_won[div_key] += 1
                earnings += prize_values[div_key]

    # Metrics Row
    net_profit = earnings - total_spent
    st.markdown("### Simulation Summary")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Spent", f"${total_spent:,.2f}")
    m2.metric("Total Earnings", f"${earnings:,.2f}")
    m3.metric("Net Profit / Loss", f"${net_profit:,.2f}", delta=f"{net_profit:,.2f}")
    m4.metric("Return on Investment", f"{(earnings / total_spent) * 100:.2f}%" if total_spent > 0 else "0.00%")

    # Payouts Table
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

    # Visualization Tabs
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
