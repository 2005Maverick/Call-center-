import pandas as pd

# Path to the June dump Excel file
excel_path = "callcenter_dashboard/Dialer dump- June'25 (5).xlsx"

# Read Sheet1
df = pd.read_excel(excel_path, sheet_name="Sheet1")

# Remove empty or summary rows (keep only rows with valid dates in the first column)
df_clean = df[df[df.columns[0]].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}")]

# If there are fewer than 100 rows, use all; else, sample 100
if len(df_clean) > 100:
    df_sample = df_clean.sample(n=100, random_state=42)
else:
    df_sample = df_clean.copy()

# Save to CSV
sample_csv_path = "callcenter_dashboard/sample_data.csv"
df_sample.to_csv(sample_csv_path, index=False)

print(f"Sample data saved to {sample_csv_path} with {len(df_sample)} rows.") 