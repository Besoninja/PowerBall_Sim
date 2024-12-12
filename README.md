# Australian PowerBall Simulator

A Streamlit-based web application that simulates Australian PowerBall lottery games and provides detailed statistical analysis of the results.

## Features

### Game Modes
- **QuickPick**: Automatically generates random numbers for each ticket
- **Marked Entry**: Allows users to select their own numbers:
  - 7 standard numbers (from 1-35)
  - 1 PowerBall number (from 1-20)

### Simulation Options
- Configure multiple tickets per game
- Run multiple games in a single simulation
- Real-time cost tracking ($1.35 per ticket)
- Accurate prize structure based on Australian PowerBall

### Results Analysis
- Comprehensive breakdown of winnings by prize division
- Total spending and earnings summary
- Downloadable results in CSV format

### Visualization Tools
1. **Winnings Histogram**
   - Visual representation of wins across different prize divisions

2. **Frequency Overview**
   - Top 7 most frequent standard balls
   - Most frequent PowerBall number

3. **Frequency Charts**
   - Distribution of standard ball appearances
   - Distribution of PowerBall appearances

4. **Sorted Frequency Analysis**
   - Sorted visualization of ball frequencies
   - Clear identification of hot and cold numbers

5. **Radial Charts**
   - Polar representation of number frequencies
   - Separate visualizations for standard balls and PowerBalls

## Prize Divisions

| Division | Winning Combination | Prize Value |
|----------|-------------------|-------------|
| 1 | 7 Standard + PowerBall | $22,852,522.41 |
| 2 | 7 Standard | $128,161.72 |
| 3 | 6 Standard + PowerBall | $6,026.19 |
| 4 | 6 Standard | $459.55 |
| 5 | 5 Standard + PowerBall | $160.45 |
| 6 | 5 Standard | $42.51 |
| 7 | 4 Standard + PowerBall | $71.58 |
| 8 | 3 Standard + PowerBall | $17.89 |
| 9 | 2 Standard + PowerBall | $10.88 |

## Requirements
- Python 3.x
- Streamlit
- Pandas
- Plotly
- Altair
- Random (Python standard library)
- Collections (Python standard library)

## Installation

```bash
pip install streamlit pandas plotly altair
```

## Usage

1. Clone the repository
2. Navigate to the project directory
3. Run the Streamlit app:
```bash
streamlit run powerball_simulator.py
```

## Disclaimer

This simulator is for educational and entertainment purposes only. It uses random number generation to simulate lottery draws and should not be used for gambling decisions. The prize values are approximations and may not reflect current actual lottery prizes.
