import requests
import csv
from datetime import datetime
import os

DTCC_API_URL = "https://pddata.dtcc.com/ppd/api/ticker/CFTC/RATES"
CSV_FILE_NAME = "trade_data.csv"

def fetch_trade_data():
    try:
        response = requests.get(DTCC_API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def get_existing_trade_timestamps():
    """Read existing trade timestamps from CSV to check for duplicates"""
    existing_timestamps = set()
    
    if not os.path.exists(CSV_FILE_NAME):
        return existing_timestamps
    
    try:
        with open(CSV_FILE_NAME, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Use trade time as unique identifier for duplication check
                trade_time = row.get('Trade Time', '')
                if trade_time:
                    existing_timestamps.add(trade_time)
    except IOError as e:
        print(f"Error reading existing CSV file: {e}")
    
    return existing_timestamps

def calculate_dv01(notional, rates, tenor_in_years):
    # This is a placeholder for Dv01 calculation.
    # A more accurate calculation would require a proper interest rate model.
    # For simplicity, we'll use a basic approximation: Dv01 = Notional * Rates * Tenor / 10000
    try:
        notional = float(str(notional).replace(',', ''))
        rates = float(rates)
        dv01 = (notional * rates * tenor_in_years) / 10000
        return round(dv01, 2)
    except (ValueError, TypeError):
        return None

def process_trades(trade_list):
    processed_data = []
    for trade in trade_list:
        trade_time = trade.get('eventTimestamp', '')
        effective_date = trade.get('effectiveDate', '')
        expiration_date = trade.get('expirationDate', '')
        currency = trade.get('notionalCurrencyLeg1', '')
        rates = trade.get('fixedRateLeg1', '') or trade.get('spreadLeg1', '')
        notionals = trade.get('notionalAmountLeg1', '')
        action_type = trade.get('actionType', '')
        event_type = trade.get('eventType', '')
        asset_class = trade.get('assetClass', '')
        upi_underlier_name = trade.get('uniqueProductIdentifierUnderlierName', '')
        frequency= trade.get('Settlement currency-Leg 1','')
        unique_product_identifier = trade.get('uniqueProductIdentifier', '')
        
        # New fields to be added
        floating_rate_payment_frequency_period_leg2 = trade.get('floatingRatePaymentFrequencyPeriodLeg2', '')
        floating_rate_payment_frequency_period_multiplier_leg2 = trade.get('floatingRatePaymentFrequencyPeriodMultiplierLeg2', '')
        dissemination_identifier = trade.get('disseminationIdentifier', '')
        original_dissemination_identifier = trade.get('originalDisseminationIdentifier', '')
        other_payment_type = trade.get('otherPaymentType', '')
        fixed_rate_payment_frequency_period_leg1 = trade.get('fixedRatePaymentFrequencyPeriodLeg1', '')
        fixed_rate_payment_frequency_period_multiplier_leg1 = trade.get('fixedRatePaymentFrequencyPeriodMultiplierLeg1', '')
        package_indicator = trade.get('packageIndicator', '')
        # Determine Tenor in years for Dv01 calculation
        tenor_in_years = None
        if effective_date and expiration_date:
            try:
                effective_dt = datetime.strptime(effective_date, '%Y-%m-%d')
                expiration_dt = datetime.strptime(expiration_date, '%Y-%m-%d')
                tenor_in_years = (expiration_dt - effective_dt).days / 365.25
            except ValueError:
                pass

        dv01 = calculate_dv01(notionals, rates, tenor_in_years) if tenor_in_years is not None else None

        processed_data.append({
            'Trade Time': trade_time,
            'Effective Date': effective_date,
            'Expiration Date': expiration_date,
            'Tenor': tenor_in_years,
            'Currency': currency,
            'Rates': rates,
            'Notionals': notionals,
            'Dv01': dv01,
            'Frequency':frequency,
            'Action Type': action_type,
            'Event Type': event_type,
            'Asset Class': asset_class,
            'UPI Underlier Name': upi_underlier_name,
            'Unique Product Identifier': unique_product_identifier,
            'Dissemination Identifier': dissemination_identifier,
            'Original Dissemination Identifier': original_dissemination_identifier,
            'Other Payment Type': other_payment_type,
            'Package Indicator': package_indicator,
            'Floating Rate Payment Frequency Period Leg2': floating_rate_payment_frequency_period_leg2,
            'Floating Rate Payment Frequency Period Multiplier Leg2': floating_rate_payment_frequency_period_multiplier_leg2,
            'Fixed Rate Payment Frequency Period Leg1': fixed_rate_payment_frequency_period_leg1,
            'Fixed Rate Payment Frequency Period Multiplier Leg1': fixed_rate_payment_frequency_period_multiplier_leg1
        })
    return processed_data

def filter_new_trades(processed_data, existing_timestamps):
    """Filter out trades that already exist in the CSV file"""
    new_trades = []
    for trade in processed_data:
        trade_time = trade.get('Trade Time', '')
        if trade_time and trade_time not in existing_timestamps:
            new_trades.append(trade)
    
    return new_trades

def append_to_csv(data):
    fieldnames = [
        'Trade Time', 'Effective Date', 'Expiration Date', 'Tenor', 'Currency',
        'Rates', 'Notionals', 'Dv01', 'Frequency', 'Action Type', 'Event Type',
        'Asset Class', 'UPI Underlier Name', 'Unique Product Identifier',
        'Dissemination Identifier', 'Original Dissemination Identifier', 'Other Payment Type', 'Package Indicator',
        'Floating Rate Payment Frequency Period Leg2', 'Floating Rate Payment Frequency Period Multiplier Leg2',
        'Fixed Rate Payment Frequency Period Leg1', 'Fixed Rate Payment Frequency Period Multiplier Leg1'
    ]
    try:
        with open(CSV_FILE_NAME, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # Write header only if the file is empty
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerows(data)
        print(f"Appended {len(data)} new trades to {CSV_FILE_NAME}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    # Get existing trade timestamps to check for duplicates
    existing_timestamps = get_existing_trade_timestamps()
    print(f"Found {len(existing_timestamps)} existing trades in CSV")
    
    json_data = fetch_trade_data()
    if json_data and 'tradeList' in json_data:
        trades = json_data['tradeList']
        processed_trades = process_trades(trades)
        
        if processed_trades:
            # Filter out existing trades
            new_trades = filter_new_trades(processed_trades, existing_timestamps)
            
            if new_trades:
                append_to_csv(new_trades)
                print(f"Total trades fetched: {len(processed_trades)}")
                print(f"New trades added: {len(new_trades)}")
                print(f"Duplicate trades skipped: {len(processed_trades) - len(new_trades)}")
            else:
                print("No new trades found. All trades already exist in CSV.")
        else:
            print("No trade data to process.")
    else:
        print("No trade data fetched or 'tradeList' not found in response.")