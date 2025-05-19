from io import BytesIO
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import pandas as pd
from datetime import datetime
from collections import defaultdict

def generate_report(data: dict) -> BytesIO:
    """Generate PDF report from data"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    y = 800
    p.drawString(50, y, "Marketing Report")
    y -= 30

    if data.get('campaigns'):
        p.drawString(50, y, "Active Campaigns:")
        y -= 20
        for campaign in data['campaigns']:
            p.drawString(70, y, f"- {campaign.get('name', 'Unnamed Campaign')}")
            y -= 15

    if data.get('offers'):
        y -= 20
        p.drawString(50, y, "Active Offers:")
        y -= 20
        for offer in data['offers']:
            p.drawString(70, y, f"- {offer[1]} (Payout: ${offer[3]})")
            y -= 15
            p.drawString(90, y, f"KPI: {offer[6]}")
            y -= 15

    if data.get('appsflyer'):
        y -= 20
        p.drawString(50, y, "AppsFlyer Report:")
        y -= 20
        p.drawString(70, y, "Campaigns:")
        y -= 15
        for campaign in data['appsflyer']['campaigns']:
            p.drawString(90, y, f"- {campaign.get('name', 'Unnamed Campaign')}")
            y -= 15

        p.drawString(70, y, "Stats:")
        y -= 15
        for stat in data['appsflyer']['stats']:
            p.drawString(90, y, f"- {stat.get('name', 'Unnamed Stat')}: {stat.get('value', 'N/A')}")
            y -= 15

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def generate_conversion_analysis(installs_data: str, events_data: str, offer_name: str, date_range: tuple) -> BytesIO:
    """Generate conversion analysis graph"""
    from_date, to_date = date_range
    
    # Parse CSV data
    installs_count = len(installs_data.splitlines()) - 1
    events_count = len(events_data.splitlines()) - 1
    
    conversion_rate = (events_count / installs_count) * 100 if installs_count else 0
    
    plt.figure(figsize=(8, 4))
    plt.bar(['Conversion'], [conversion_rate], color='#4CAF50')
    plt.title(f"Conversion for {offer_name}\n{from_date} - {to_date}")
    plt.ylabel("%")
    plt.ylim(0, 5)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_revenue_forecast(events_data: str, payout: float, date_range: tuple) -> BytesIO:
    """Generate revenue forecast graph"""
    from_date, to_date = date_range
    
    # Parse events by date
    date_events = defaultdict(int)
    for line in events_data.splitlines()[1:]:
        parts = line.split(',')
        if len(parts) >= 4:
            event_time = parts[3].strip()
            try:
                date_str = event_time.split(' ')[0]
                date_events[date_str] += 1
            except (IndexError, AttributeError):
                continue

    # Create time series
    date_range = pd.date_range(start=from_date, end=to_date)
    df = pd.DataFrame(index=date_range, columns=['events'], data=0)
    
    for date_str, count in date_events.items():
        try:
            date = pd.to_datetime(date_str)
            if date in df.index:
                df.loc[date, 'events'] = count
        except pd.errors.ParserError:
            continue

    df['revenue'] = df['events'] * payout

    if len(df) < 5:
        raise ValueError("Insufficient data (minimum 5 days required)")

    # Polynomial regression for forecast
    X = np.arange(len(df)).reshape(-1, 1)
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    model = LinearRegression().fit(X_poly, df['revenue'])

    # Forecast next 7 days
    forecast_days = 7
    X_future = poly.transform(np.arange(len(df), len(df) + forecast_days).reshape(-1, 1))
    forecast = model.predict(X_future)
    forecast = np.maximum(forecast, 0)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['revenue'], 'o-', label='Historical Data')
    plt.plot(
        pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=forecast_days),
        forecast,
        'r--',
        marker='o',
        label=f'7-day Forecast'
    )
    plt.title(f"Revenue Forecast\nPayout: ${payout}/event")
    plt.xlabel("Date")
    plt.ylabel("Revenue ($)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf

def generate_trend_analysis(installs_data: str, date_range: tuple, offer_name: str) -> BytesIO:
    """Generate trend analysis graph"""
    from_date, to_date = date_range
    
    # Parse data
    date_counts = {}
    for line in installs_data.splitlines()[1:]:
        parts = line.split(',')
        if len(parts) >= 2:
            date_str = parts[1].split(' ')[0]
            date_counts[date_str] = date_counts.get(date_str, 0) + 1

    if not date_counts:
        raise ValueError("Insufficient data for trend analysis")

    # Sort dates
    parsed_dates = sorted(date_counts.keys())
    installs = [date_counts[date] for date in parsed_dates]

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(parsed_dates, installs, marker='o', linestyle='-', color='#2196F3')
    plt.title(f"Install Trends: {offer_name}\n{from_date} - {to_date}")
    plt.xlabel("Date")
    plt.ylabel("Installs")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf 