import os
import pandas as pd
from pathlib import Path

def process_patent_zips(raw_data_dir: str) -> pd.DataFrame:
    """
    Reads annualized USPTO patent ZIP files, filters for US inventors,
    and calculates pre-trend and post-shock innovation deltas per county.
    """
    raw_path = Path(raw_data_dir)
    zip_files = sorted(raw_path.glob("*.zip"))
    
    if not zip_files:
        raise FileNotFoundError(f"No .zip files found in {raw_data_dir}. Check your path.")
    
    print(f"Found {len(zip_files)} zip files. Beginning memory-optimized load...")
    
    # The exact columns we need to prevent RAM crashes
    cols_to_keep = ['patent_number', 'application_year', 'country', 'state', 'county']
    df_list = []
    
    # 1. Load and concatenate all zip files
    for file in zip_files:
        print(f"  -> Loading {file.name}...")
        try:
            # Pandas natively unzips and reads the CSV inside
            temp_df = pd.read_csv(
                file, 
                usecols=cols_to_keep, 
                dtype={'application_year': 'Int64'} # Handles potential NaNs in years gracefully
            )
            df_list.append(temp_df)
        except Exception as e:
            print(f"  [!] Error reading {file.name}: {e}")
            
    # Combine all years into one massive DataFrame
    print("Concatenating data...")
    full_df = pd.concat(df_list, ignore_index=True)
    
    # 2. Filter and clean
    print("Filtering for US inventors and dropping missing geographies...")
    us_df = full_df[full_df['country'] == 'US'].copy()
    us_df = us_df.dropna(subset=['state', 'county', 'application_year'])
    
    # 3. Group by County and Year
    print("Counting unique patents per county per year...")
    grouped = us_df.groupby(['state', 'county', 'application_year'])['patent_number'].nunique().reset_index()
    
    # 4. Pivot the table so years become columns
    print("Pivoting panel data...")
    pivot_df = grouped.pivot(
        index=['state', 'county'], 
        columns='application_year', 
        values='patent_number'
    ).fillna(0) # If a county had 0 patents in a year, fill with 0
    
    # 5. Calculate the regression variables
    print("Calculating pre-trend and post-shock deltas...")
    
    # Ensure all required year columns exist to prevent KeyError
    required_years = [2014, 2017, 2021, 2022, 2023]
    for year in required_years:
        if year not in pivot_df.columns:
            pivot_df[year] = 0

    # Falsification target: 2017 minus 2014
    pivot_df['delta_pre_trend'] = pivot_df[2017] - pivot_df[2014]
    
    # Main regression target: Average of (2021, 2022, 2023) minus 2017
    # (We average the post-shock years to smooth out single-year volatility)
    pivot_df['delta_post_shock'] = pivot_df[[2021, 2022, 2023]].mean(axis=1) - pivot_df[2017]
    
    # Clean up the index to make it a flat DataFrame again
    final_df = pivot_df.reset_index()
    
    # Ensure column names are strings, not integers, for easier merging later
    final_df.columns = [str(col) if isinstance(col, int) else col for col in final_df.columns]
    
    print(f"Success! Generated local innovation panel with {len(final_df)} counties.")
    
    return final_df

# --- Quick Test Block ---
# If you run this script directly, it will test the function.
if __name__ == "__main__":
    # Adjust this path if your terminal is in a different directory
    test_data_dir = "data/raw" 
    
    if os.path.exists(test_data_dir):
        df_out = process_patent_zips(test_data_dir)
        print(df_out.head())
        # Save the processed data
        # df_out.to_csv("../data/processed/local_innovation_outcomes.csv", index=False)
    else:
        print("Test skipped: Raw data directory not found.")