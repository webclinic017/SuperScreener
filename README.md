# Stock Screener

This project is a super screener strategy automation that helps identify potential trading opportunities based on specific criteria.

## Overview

The stock screener analyzes a list of stock symbols and filters them based on predefined conditions. It uses historical stock data and calculates various indicators to determine whether a stock should be considered for long or short positions.

## Features

- **Stock Screening**: The program fetches historical stock data using the Yahoo Finance API, calculates percentage returns, and screens stocks based on user-defined threshold values.
- **Pivot Calculation**: The program calculates pivot points for short-listed stocks to identify potential support and resistance levels.
- **Order Placement**: The program places buy/sell orders for stocks that meet specific criteria, such as open price, previous day's high/low, resistance/support levels, and percentage change.

## Setup

1. Clone the repository: `git clone <repository_url>`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Configure the settings in the `config.yaml` file, including threshold values, target time, starting capital, and other parameters.
4. Provide a list of stock symbols in the `data/universe.csv` file.
5. Run the main script: `python main.py` (Make sure main.py run before market open time.)

## Configuration

The `config.yaml` file contains various settings and parameters for the stock screener. You can modify these values according to your requirements. Here are the key configuration options:

- `target_time`: The target time to start scanning for potential trades.
- `starting_capital`: The initial amount of capital available for trading.

## Results

After running the script, the program will generate a DataFrame with the short-listed stocks and their respective pivot points. The program will also place buy/sell orders for stocks that meet the specified conditions.
