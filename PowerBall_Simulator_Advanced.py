import random
import streamlit as st
import pandas as pd
from collections import OrderedDict
import plotly.graph_objects as go
import altair as alt

# Define the available balls
blue_ball = list(range(1, 36))
power_ball = list(range(1, 21))

st.title('Australian PowerBall Simulator')

# Game Mode selection
game_mode = st.radio("Game Mode:", ['QuickPick', 'Marked Entry'])

# Number of tickets and games
tickets = st.number_input('Tickets:', min_value=1, value=1)
games = st.number_input('Games:', min_value=1, value=1)

# Update the labels for display
times_won_labels = {
    "7+P": "7 Standard Balls + PowerBall",
    "7": "7 Standard Balls",
    "6+P": "6 Standard Balls + PowerBall",
    "6": "6 Standard Balls",
    "5+P": "5 Standard Balls + PowerBall",
    "5": "5 Standard Balls",
    "4+P": "4 Standard Balls + PowerBall",
    "3+P": "3 Standard Balls + PowerBall",
    "2+P": "2 Standard Balls + PowerBall"
}

# Add prize values for simulated payouts
prize_values = {
    "7+P": 22852522.41,
    "7": 128161.72,
    "6+P": 6026.19,
    "6": 459.55,
    "5+P": 160.45,
    "5": 42.51,
    "4+P": 71.58,
    "3+P": 17.89,
    "2+P": 10.88
}

# User selects numbers for 'Marked Entry' game mode
user_blues = set()
user_PB = None

if game_mode == 'Marked Entry':
    st.write('Select 7 Numbers:')
    user_blues = st.multiselect('Select 7 Numbers:', blue_ball, max_selections=7)
    if len(user_blues) != 7:
        st.warning("Please select exactly 7 numbers.")
    user_PB = st.selectbox('Select Powerball:', power_ball)

if st.button('Play Games'):
    # Initialize counters
    total_spent = 0
    earnings = 0
    times_won = {
        "7+P": 0,
        "7": 0,
        "6+P": 0,
        "6": 0,
        "5+P": 0,
        "5": 0,
        "4+P": 0,
        "3+P": 0,
        "2+P": 0
    }

    # Initialize frequency trackers
    standard_ball_frequency = {ball: 0 for ball in blue_ball}
    power_ball_frequency = {ball: 0 for ball in power_ball}

    # Validate Marked Entry
    if game_mode == 'Marked Entry' and len(user_blues) != 7:
        st.error("You need to select exactly 7 Standard balls to proceed.")
    else:
        # Run the simulation
        for _ in range(games):
            winning_blues = set(random.sample(blue_ball, 7))
            winning_PB = random.choice(power_ball)

            # Track frequencies
            for wb in winning_blues:
                standard_ball_frequency[wb] += 1
            power_ball_frequency[winning_PB] += 1

            winning_numbers = {'blues': winning_blues, 'PB': winning_PB}

            for ticket in range(tickets):
                total_spent += 1.35
                # Determine user's numbers
                if game_mode == 'QuickPick':
                    my_blues = set(random.sample(blue_ball, 7))
                    my_PB = random.choice(power_ball)
                else:
                    my_blues = set(user_blues)
                    my_PB = user_PB

                # Calculate winnings
                blue_matches = len(my_blues.intersection(winning_numbers['blues']))
                power_matches = (my_PB == winning_numbers['PB'])

                win_amt = 0
                if blue_matches == 7:
                    if power_matches:
                        win_amt = prize_values["7+P"]
                        times_won['7+P'] += 1
                    else:
                        win_amt = prize_values["7"]
                        times_won['7'] += 1
                elif blue_matches == 6:
                    if power_matches:
                        win_amt = prize_values["6+P"]
                        times_won['6+P'] += 1
                    else:
                        win_amt = prize_values["6"]
                        times_won['6'] += 1
                elif blue_matches == 5:
                    if power_matches:
                        win_amt = prize_values["5+P"]
                        times_won['5+P'] += 1
                    else:
                        win_amt = prize_values["5"]
                        times_won['5'] += 1
                elif blue_matches == 4:
                    if power_matches:
                        win_amt = prize_values["4+P"]
                        times_won['4+P'] += 1
                elif blue_matches == 3:
                    if power_matches:
                        win_amt = prize_values["3+P"]
                        times_won['3+P'] += 1
                elif blue_matches == 2:
                    if power_matches:
                        win_amt = prize_values["2+P"]
                        times_won['2+P'] += 1

                earnings += win_amt

        # Reorder results
        ordered_times_won = OrderedDict((key, times_won[key]) for key in times_won_labels)
        table_data = [
            {
                "Winning Combination": times_won_labels[key],
                "Earnings Per Draw": f"${prize_values[key]:,.2f}",
                "Count": value,
                "Simulated Payout": f"${value * prize_values[key]:,.2f}"
            }
            for key, value in ordered_times_won.items()
        ]

        # Display the totals and table
        st.subheader("Totals for this run")
        st.write(f"Total Spent: ${total_spent:.2f}")
        st.write(f"Total Earnings: ${earnings:.2f}")
        
        st.subheader("Winnings Breakdown")
        st.table(table_data)

        df_table = pd.DataFrame(table_data)

        st.download_button(
            "Download Results as CSV",
            df_table.to_csv(index=False),
            "results.csv",
            "text/csv"
        )

        # Create tabs for visualizations
        winnings_histogram_tab, tab1, tab2, tab3, tab4 = st.tabs([
            "Winnings Histogram",
            "Frequency Overview",
            "Frequency Charts",
            "Sorted Frequency",
            "Radial Charts"
        ])

        # Winnings Histogram Tab
        with winnings_histogram_tab:
            st.subheader("Winnings Histogram")
            st.bar_chart(df_table.set_index("Winning Combination")["Count"])

        # Frequency Overview
        with tab1:
            # Compute top 7 standard and top 1 power
            top_7_standard = sorted(standard_ball_frequency.items(), key=lambda x: x[1], reverse=True)[:7]
            top_1_power = sorted(power_ball_frequency.items(), key=lambda x: x[1], reverse=True)[:1]

            st.subheader("Most Frequent Numbers (from all games)")
            st.write(f"Top 7 Standard Balls: {[num for num, freq in top_7_standard]}")
            st.write(f"Top 1 PowerBall: {top_1_power[0][0] if top_1_power else 'None'}")

        # Frequency Histogram
        with tab2:
            df_standard = pd.DataFrame(list(standard_ball_frequency.items()), columns=["Ball", "Count"])
            df_power = pd.DataFrame(list(power_ball_frequency.items()), columns=["Ball", "Count"])

            st.subheader("Frequency Charts")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Standard Ball Frequency")
                st.bar_chart(df_standard.set_index("Ball")["Count"])
            with col2:
                st.write("PowerBall Frequency")
                st.bar_chart(df_power.set_index("Ball")["Count"])

        # Sorted Frequency Histogram - Using altair module
        with tab3:
            df_standard_sorted = pd.DataFrame(list(standard_ball_frequency.items()), columns=["Ball", "Count"])
            df_power_sorted = pd.DataFrame(list(power_ball_frequency.items()), columns=["Ball", "Count"])

            # Sort the balls in a descending fashion by "Count"
            df_standard_sorted = df_standard_sorted.sort_values(by="Count", ascending=False)
            df_power_sorted = df_power_sorted.sort_values(by="Count", ascending=False)

            st.subheader("Sorted Frequency (Most Frequent to Least Frequent)")

            col1, col2 = st.columns(2)
            with col1:
                st.write("Standard Balls (Sorted)")
                chart_standard = alt.Chart(df_standard_sorted).mark_bar().encode(
                    x=alt.X('Ball:N', sort=None),  # 'N'=Nominal, 'sort=None' ensures the order, as described above, is maintained
                    y=alt.Y('Count:Q', axis=alt.Axis(format='d'))  # Ensure only integers are displayed
                )
                st.altair_chart(chart_standard, use_container_width=True)

            with col2:
                st.write("PowerBalls (Sorted)")
                chart_power = alt.Chart(df_power_sorted).mark_bar().encode(
                    x=alt.X('Ball:N', sort=None),
                    y=alt.Y('Count:Q', axis=alt.Axis(format='d'))
                )
                st.altair_chart(chart_power, use_container_width=True)

        # Radial Charts - Using plotly.graph_objects.Scatterpolar
        with tab4:
            st.subheader("Radial Charts")

            # Radar chart for the Standard balls (1–35)
            categories_standard = [str(i) for i in range(1,36)]
            values_standard = [standard_ball_frequency[i] for i in range(1,36)]

            fig_standard = go.Figure(go.Scatterpolar(
                r=values_standard,
                theta=categories_standard,
                fill='toself',
                name='Standard Ball Frequency (1-35)'
            ))
            # Radar design
            fig_standard.update_layout(
                polar=dict(
                    angularaxis=dict(type='category', tickvals=categories_standard, ticktext=categories_standard, tickfont=dict(color='black'), direction='clockwise', rotation=90),
                    radialaxis=dict(visible=True)
                ),
                showlegend=False
            )

            # Radar chart for the PowerBalls (1–20)
            categories_power = [str(i) for i in range(1,21)]
            values_power = [power_ball_frequency[i] for i in range(1,21)]

            fig_power = go.Figure(go.Scatterpolar(
                r=values_power,
                theta=categories_power,
                fill='toself',
                name='PowerBall Frequency (1-20)'
            ))
            # Radar design
            fig_power.update_layout(
                polar=dict(
                    angularaxis=dict(type='category', tickvals=categories_power, ticktext=categories_power, tickfont=dict(color='black'), direction='clockwise', rotation=90),
                    radialaxis=dict(visible=True)
                ),
                showlegend=False
            )

            col_rad1, col_rad2 = st.columns(2)
            with col_rad1:
                st.plotly_chart(fig_standard, use_container_width=True)
            with col_rad2:
                st.plotly_chart(fig_power, use_container_width=True)
