#!/usr/bin/env python3
"""
DTCC Trade Analysis Script
Replicates the combined functionality of IRSTradeParser.py and IRSTradeAnalysis.py
for DTCC trade data from DTCCParser.py output
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import combinations
from collections import defaultdict
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DTCCAnalysis:
    def __init__(self, input_file='trade_data.csv', output_file='structured_output.csv'):
        self.input_file = input_file
        self.output_file = output_file
        self.df = None
        self.structured_output = []
        
    def clean_numeric_value(self, value):
        """Clean and convert numeric values, handling DTCC-specific formatting"""
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        
        try:
            str_value = str(value).strip()
            str_value = str_value.replace(',', '')    # Remove commas
            str_value = str_value.replace('+', '')    # Remove plus signs
            str_value = str_value.replace('$', '')    # Remove dollar signs
            str_value = str_value.replace('%', '')    # Remove percent signs
            
            if str_value == '' or str_value == 'nan':
                return 0.0
            
            return float(str_value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value to float: {value}, returning 0.0")
            return 0.0
    
    def extract_tenor(self, row):
        """Extract tenor from DTCC data (UPI name or calculate from dates)"""
        # Try UPI Underlier Name first
        upi = str(row.get('UPI Underlier Name', ''))
        
        # Look for patterns like "5Y", "10Y", etc.
        tenor_match = re.search(r'(\d+)Y', upi.upper())
        if tenor_match:
            return f"{tenor_match.group(1)}Y"
        
        # Look for patterns like "5YR", "10YR", etc.
        tenor_match = re.search(r'(\d+)YR', upi.upper())
        if tenor_match:
            return f"{tenor_match.group(1)}Y"
        
        # Calculate from dates
        try:
            start = pd.to_datetime(row['Effective Date'])
            end = pd.to_datetime(row['Expiration Date'])
            years = (end - start).days / 365.25
            
            if years < 1.0:
                # For trades less than 1 year, show months
                months = int(round(years * 12))
                return f"{months}M"
            else:
                # For trades 1 year or more, show years
                return f"{int(round(years))}Y"
        except:
            return "Unknown"
    
    def get_imm_code(self, date):
        """Get IMM code for date (H, M, U, Z + year)"""
        imm_months = {3: 'H', 6: 'M', 9: 'U', 12: 'Z'}
        if date.month in imm_months and 15 <= date.day <= 21 and date.weekday() == 2:
            year = str(date.year)[-1]
            return f"{imm_months[date.month]}{year}"
        return None
    
    def get_effective_bucket(self, start_date, today):
        """Convert start date to market convention (Spot, IMM, 1Y, etc.)"""
        delta_days = (start_date - today).days
        
        if abs(delta_days) <= 5:
            return "Spot"
        
        # Check for IMM dates
        imm_code = self.get_imm_code(start_date)
        if imm_code:
            return imm_code
        
        # Check for standard periods
        months_delta = round(delta_days / 30.4375)  # average days per month
        if abs(months_delta - 6) <= 1:
            return "6M"
        if abs(months_delta - 9) <= 1:
            return "9M"
        if abs(months_delta - 12) <= 1:
            return "1Y"
        
        # Check for yearly periods
        rel_years = delta_days / 365.25
        for y in range(1, 11):
            if abs(rel_years - y) <= 0.2:
                return f"{y}Y"
        
        return start_date.strftime('%Y-%m-%d')
    
    def tenor_key(self, tenor):
        """Convert tenor to numeric key for sorting"""
        try:
            return float(tenor.strip('Y').replace('M', '0'))
        except:
            return float('inf')
    
    def compute_metric(self, structure, rates):
        """Calculate spread/butterfly metrics in basis points"""
        try:
            if structure == 'Spread':
                return round(100 * (rates[1] - rates[0]), 1)
            if structure == 'Butterfly':
                return round(100 * (2 * rates[1] - rates[0] - rates[2]), 1)
        except:
            return ''
        return ''
    
    def valid_spread(self, dv01s, tenors):
        """Validate if trades form a valid spread (DV01 neutral)"""
        if len(set(tenors)) != 2 or len(dv01s) != 2 or 0 in dv01s:
            return False
        return 0.95 <= dv01s[0] / dv01s[1] <= 1.05
    
    def valid_butterfly(self, dv01s, tenors):
        """Validate if trades form a valid butterfly (DV01 neutral)"""
        if len(set(tenors)) != 3 or len(dv01s) != 3 or 0 in dv01s:
            return False
        wings = sorted(dv01s)
        return 0.95 <= wings[0] / wings[1] <= 1.05 and 0.95 <= wings[0] * 2 / wings[2] <= 1.05
    
    def load_and_prepare_data(self):
        """Load DTCC data and prepare for analysis"""
        try:
            self.df = pd.read_csv(self.input_file)
            logger.info(f"Loaded {len(self.df)} trades from {self.input_file}")
            
            # Clean and prepare data
            self.df['Trade Time'] = pd.to_datetime(self.df['Trade Time']).dt.floor('min')
            self.df['Effective Date'] = pd.to_datetime(self.df['Effective Date'])
            self.df['Expiration Date'] = pd.to_datetime(self.df['Expiration Date'], errors='coerce')
            
            # Clean numeric fields
            self.df['Rate'] = self.df['Rates'].apply(self.clean_numeric_value)
            self.df['Notional'] = self.df['Notionals'].apply(self.clean_numeric_value)
            self.df['DV01(USD)'] = self.df['Dv01'].apply(self.clean_numeric_value)
            
            # Clean Currency field - handle NaN values
            self.df['Currency'] = self.df['Currency'].fillna('UNKNOWN')
            self.df = self.df[self.df['Currency'] != 'UNKNOWN']  # Remove records with unknown currency
            
            # Extract tenors
            self.df['T'] = self.df.apply(self.extract_tenor, axis=1)
            
            # Calculate effective buckets
            today = pd.to_datetime(datetime.today().date())
            self.df['Effective Bucket'] = self.df['Effective Date'].apply(
                lambda d: self.get_effective_bucket(d, today)
            )
            
            # Create grouping keys and trade IDs
            self.df['Trade ID'] = self.df.index
            self.df['Group Key'] = self.df.apply(
                lambda row: f"{row['Trade Time']}|{row['Effective Date']}|{row['Currency']}", 
                axis=1
            )
            
            # Handle Other Pay Type
            self.df['Other Pay Type'] = self.df.get('Other Payment Type', '').fillna('')
            
            logger.info("Data preparation completed")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def detect_structures(self):
        """Detect trade structures (butterflies, spreads, outrights, unwinds)"""
        today = pd.to_datetime(datetime.today().date())
        
        for key, group in self.df.groupby('Group Key'):
            used_ids = set()
            records = group.to_dict('records')
            
            # Detect Butterflies (3 trades)
            for triplet in combinations(records, 3):
                ids = [t['Trade ID'] for t in triplet]
                if any(i in used_ids for i in ids):
                    continue
                
                # Sort by tenor for consistent ordering
                triple_data = sorted(zip(
                    [t['T'] for t in triplet],
                    [float(t['Rate']) for t in triplet],
                    [float(t['DV01(USD)']) for t in triplet],
                    [t['Notional'] for t in triplet],
                    [str(t.get('Other Pay Type', '')) for t in triplet]
                ), key=lambda x: self.tenor_key(x[0]))
                
                tenors, rates, dv01s, notionals, pay_types = zip(*triple_data)
                
                if self.valid_butterfly(dv01s, tenors):
                    pay_type_out = 'UFRO' if any(p.strip().upper() == 'UFRO' for p in pay_types) else ', '.join(pay_types)
                    
                    self.structured_output.append({
                        'Trade Time': triplet[0]['Trade Time'],
                        'Structure': 'Butterfly',
                        'Start Date': triplet[0]['Effective Bucket'],
                        'Currency': triplet[0]['Currency'],
                        'Tenors': ', '.join(tenors),
                        'Rates': ', '.join(map(str, rates)),
                        'Notionals': ', '.join(map(str, notionals)),
                        'DV01s': ', '.join(map(str, dv01s)),
                        'Package Price': triplet[0].get('Package Price', ''),
                        'Other Pay Types': pay_type_out,
                        'Metric (bps)': self.compute_metric('Butterfly', rates),
                        'Expiration': triplet[0].get('Expiration Date', '')
                    })
                    used_ids.update(ids)
            
            # Detect Spreads (2 trades from unused)
            unused = [t for t in records if t['Trade ID'] not in used_ids]
            for pair in combinations(unused, 2):
                ids = [t['Trade ID'] for t in pair]
                if any(i in used_ids for i in ids):
                    continue
                
                # Sort by tenor for consistent ordering
                pair_data = sorted(zip(
                    [t['T'] for t in pair],
                    [float(t['Rate']) for t in pair],
                    [float(t['DV01(USD)']) for t in pair],
                    [t['Notional'] for t in pair],
                    [str(t.get('Other Pay Type', '')) for t in pair]
                ), key=lambda x: self.tenor_key(x[0]))
                
                tenors, rates, dv01s, notionals, pay_types = zip(*pair_data)
                
                if self.valid_spread(dv01s, tenors):
                    pay_type_out = 'UFRO' if any(p.strip().upper() == 'UFRO' for p in pay_types) else ', '.join(pay_types)
                    
                    self.structured_output.append({
                        'Trade Time': pair[0]['Trade Time'],
                        'Structure': 'Spread',
                        'Start Date': pair[0]['Effective Bucket'],
                        'Currency': pair[0]['Currency'],
                        'Tenors': ', '.join(tenors),
                        'Rates': ', '.join(map(str, rates)),
                        'Notionals': ', '.join(map(str, notionals)),
                        'DV01s': ', '.join(map(str, dv01s)),
                        'Package Price': pair[0].get('Package Price', ''),
                        'Other Pay Types': pay_type_out,
                        'Metric (bps)': self.compute_metric('Spread', rates),
                        'Expiration': pair[0].get('Expiration Date', '')
                    })
                    used_ids.update(ids)
            
            # Remaining trades (Outrights or Unwinds)
            for rec in records:
                if rec['Trade ID'] in used_ids:
                    continue
                
                # Determine if Unwind or Outright
                structure = 'Unwind' if rec['Effective Date'] < today else 'Outright'
                
                self.structured_output.append({
                    'Trade Time': rec['Trade Time'],
                    'Structure': structure,
                    'Start Date': rec['Effective Bucket'],
                    'Currency': rec['Currency'],
                    'Tenors': rec['T'],
                    'Rates': rec['Rate'],
                    'Notionals': rec['Notional'],
                    'DV01s': rec['DV01(USD)'],
                    'Package Price': rec.get('Package Price', ''),
                    'Other Pay Types': 'UFRO' if str(rec.get('Other Pay Type', '')).strip().upper() == 'UFRO' else rec.get('Other Pay Type', ''),
                    'Metric (bps)': '',
                    'Expiration': rec.get('Expiration Date', '')
                })
        
        logger.info(f"Detected {len(self.structured_output)} structured trades")
    
    def save_structured_output(self):
        """Save structured output to CSV (equivalent to IRSTradeParser output)"""
        if not self.structured_output:
            logger.error("No structured output to save")
            return False
        
        df_output = pd.DataFrame(self.structured_output)
        df_output.to_csv(self.output_file, index=False)
        logger.info(f"Saved structured output to {self.output_file}")
        return True
    
    def format_dv01(self, dv01_value):
        """Format DV01 value in thousands"""
        rounded = int(round(dv01_value / 1000.0))
        return f"{rounded}k" if rounded > 0 else None
    
    def generate_commentary(self, currency='USD'):
        """Generate market commentary (equivalent to IRSTradeAnalysis output)"""
        if not self.structured_output:
            return f"^^{currency.upper()} SDR deals today^^\n\nNo structured data available for commentary"
        
        df = pd.DataFrame(self.structured_output)
        df = df[df['Currency'] == currency.upper()]
        
        if df.empty:
            return f"^^{currency.upper()} SDR deals today^^\n\nNo {currency.upper()} trades found"
        
        # Normalize columns
        df['Structure'] = df['Structure'].fillna('')
        df['Start Date'] = df['Start Date'].astype(str)
        df['Expiration'] = pd.to_datetime(df['Expiration'], errors='coerce')
        
        output = [f"^^{currency.upper()} SDR deals today^^"]
        
        # --- Outright Commentary ---
        outright_df = df[df['Structure'].isin(['Outright', 'Unwind'])].copy()
        if not outright_df.empty:
            outright_df['SortKey'] = outright_df['Expiration'].fillna(pd.Timestamp.max)
            outright_df.sort_values(by='SortKey', inplace=True)
            outright_groups = defaultdict(list)
            
            for _, row in outright_df.iterrows():
                key = f"{row['Start Date']} - {row['Tenors']}"
                outright_groups[key].append(row)
            
            if outright_groups:
                output.append(f"\n^^{currency.upper()} Outrights^^")
                for label in outright_groups:
                    trades = outright_groups[label]
                    dv01_total = sum(float(t['DV01s']) for t in trades if pd.notna(t['DV01s']))
                    formatted_dv01 = self.format_dv01(dv01_total)
                    if not formatted_dv01:
                        continue
                    
                    rates = [float(t['Rates']) for t in trades if str(t['Other Pay Types']).strip().upper() != 'UFRO']
                    if rates:
                        min_rate, max_rate = min(rates), max(rates)
                        if min_rate != max_rate:
                            rate_range = f" (Rate range: {min_rate:.4f}–{max_rate:.4f})"
                        else:
                            rate_range = f" (Rate: {min_rate:.4f})"
                        output.append(f"{label} traded {formatted_dv01} DV01{rate_range}")
                    else:
                        output.append(f"{label} traded {formatted_dv01} DV01")
        
        # --- Spread Commentary ---
        spread_df = df[df['Structure'] == 'Spread']
        if not spread_df.empty:
            spread_groups = defaultdict(list)
            for _, row in spread_df.iterrows():
                tenors = sorted(t.strip() for t in row['Tenors'].split(','))
                pair = f"{tenors[0]} vs {tenors[1]}"
                key = (pair, row['Start Date'])
                spread_groups[key].append(row)
            
            if spread_groups:
                output.append(f"\n^^{currency.upper()} Spreads^^")
                pairs_ordered = sorted(set(k[0] for k in spread_groups.keys()))
                for pair in pairs_ordered:
                    output.append(f"\n^^{pair}^^")
                    # Process all groups for this pair
                    pair_groups = [(p, eff, rows) for (p, eff), rows in spread_groups.items() if p == pair]
                    for (p, eff, rows) in pair_groups:
                        total_dv01 = sum(float(r['DV01s'].split(',')[0]) for r in rows)
                        formatted_dv01 = self.format_dv01(total_dv01)
                        if not formatted_dv01:
                            # Show small DV01s as "<1k" instead of skipping
                            formatted_dv01 = "<1k"
                        
                        bps_vals = [float(r['Metric (bps)']) for r in rows 
                                   if pd.notna(r['Metric (bps)']) and r['Metric (bps)'] != '' 
                                   and str(r['Other Pay Types']).strip().upper() != 'UFRO']
                        if bps_vals:
                            min_bps, max_bps = min(bps_vals), max(bps_vals)
                            if min_bps != max_bps:
                                bps_part = f" (Rate range: {min_bps:.1f}–{max_bps:.1f} bps)"
                            else:
                                bps_part = f" (Rate: {min_bps:.1f} bps)"
                            output.append(f"{eff} - {pair} traded {formatted_dv01} DV01{bps_part}")
                        else:
                            output.append(f"{eff} - {pair} traded {formatted_dv01} DV01")
        
        # --- Butterfly Commentary ---
        butterfly_df = df[df['Structure'] == 'Butterfly']
        if not butterfly_df.empty:
            butterfly_groups = defaultdict(list)
            for _, row in butterfly_df.iterrows():
                tenors = sorted((t.strip() for t in row['Tenors'].split(',')), 
                               key=lambda x: self.tenor_key(x))
                label = f"{tenors[0]} vs {tenors[1]} vs {tenors[2]}"
                key = (label, row['Start Date'])
                butterfly_groups[key].append(row)
            
            if butterfly_groups:
                output.append(f"\n^^{currency.upper()} Butterflies^^")
                flies_ordered = sorted(set(k[0] for k in butterfly_groups.keys()))
                for label in flies_ordered:
                    output.append(f"\n^^{label}^^")
                    # Process all groups for this label
                    label_groups = [(triplet, eff, rows) for (triplet, eff), rows in butterfly_groups.items() if triplet == label]
                    for (triplet, eff, rows) in label_groups:
                        max_dv01s = [max(float(x) for x in r['DV01s'].split(',')) for r in rows]
                        total_dv01 = sum(max_dv01s)
                        formatted_dv01 = self.format_dv01(total_dv01)
                        if not formatted_dv01:
                            # Show small DV01s as "<1k" instead of skipping
                            formatted_dv01 = "<1k"
                        
                        bps_vals = [float(r['Metric (bps)']) for r in rows 
                                   if pd.notna(r['Metric (bps)']) and r['Metric (bps)'] != '' 
                                   and str(r['Other Pay Types']).strip().upper() != 'UFRO']
                        if bps_vals:
                            min_bps, max_bps = min(bps_vals), max(bps_vals)
                            if min_bps != max_bps:
                                bps_part = f" (Rate range: {min_bps:.1f}–{max_bps:.1f} bps)"
                            else:
                                bps_part = f" (Rate: {min_bps:.1f} bps)"
                            output.append(f"{eff} - {triplet} traded {formatted_dv01} DV01{bps_part}")
                        else:
                            output.append(f"{eff} - {triplet} traded {formatted_dv01} DV01")
        
        return '\n'.join(output)
    
    def run_analysis(self, currencies=['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD']):
        """Run complete analysis pipeline"""
        logger.info("Starting DTCC trade analysis...")
        
        # Load and prepare data
        if not self.load_and_prepare_data():
            return False
        
        # Detect structures
        self.detect_structures()
        
        # Save structured output
        if not self.save_structured_output():
            return False
        
        # Generate commentary for each currency
        commentary_results = {}
        for currency in currencies:
            commentary = self.generate_commentary(currency)
            commentary_results[currency] = commentary
            
            # Save individual currency commentary
            filename = f'{currency.lower()}_commentary.txt'
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(commentary)
                logger.info(f"Generated commentary for {currency} -> {filename}")
            except Exception as e:
                logger.error(f"Failed to write {filename}: {e}")
        
        # Save combined commentary
        combined_commentary = '\n\n' + '='*80 + '\n\n'.join(
            commentary_results[curr] for curr in currencies if 'No' not in commentary_results[curr]
        )
        
        try:
            with open('market_commentary.txt', 'w', encoding='utf-8') as f:
                f.write(combined_commentary)
            logger.info("Generated market_commentary.txt")
        except Exception as e:
            logger.error(f"Failed to write market_commentary.txt: {e}")
        
        logger.info("Analysis completed successfully")
        return True

def main():
    """Main execution function"""
    analyzer = DTCCAnalysis()
    
    # Run analysis for all supported currencies including Asian markets
    success = analyzer.run_analysis(['USD', 'EUR', 'GBP', 'JPY', 'INR', 'SGD', 'AUD', 'THB', 'TWD', 'KRW', 'HKD'])
    
    if success:
        print("DTCC Analysis completed successfully!")
        print("Generated files:")
        print("- structured_output.csv (equivalent to IRSTradeParser output)")
        print("- market_commentary.txt (equivalent to IRSTradeAnalysis output)")
        print("- Individual currency commentary files")
    else:
        print("Analysis failed. Check logs for details.")

if __name__ == "__main__":
    main()

