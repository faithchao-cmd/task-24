"""
Cleans the raw Superstore data based on the audit findings and writes
a cleaned sample for review.
"""
import pandas as pd
import numpy as np

df = pd.read_csv("/mnt/user-data/outputs/superstore_raw.csv")
n_before = len(df)
actions = []

# 1. Drop exact duplicate rows
before = len(df)
df = df.drop_duplicates(keep="first")
actions.append(("Removed exact duplicate rows", before - len(df)))

# 2. Standardize text formatting: trim whitespace, Title Case
for col in ["State", "City"]:
    before_vals = df[col].copy()
    df[col] = df[col].astype(str).str.strip().str.title()
    changed = (before_vals.astype(str) != df[col]).sum()
    actions.append((f"Standardized formatting in {col}", int(changed)))

# 3. Fix Ship Date < Order Date by setting Ship Date = Order Date + 2 days (flagged, not guessed silently)
od = pd.to_datetime(df["Order Date"], errors="coerce")
sd = pd.to_datetime(df["Ship Date"], errors="coerce")
bad_mask = sd.notna() & od.notna() & (sd < od)
df["DQ_Flag_ShipDate_Corrected"] = bad_mask
df.loc[bad_mask, "Ship Date"] = (od[bad_mask] + pd.Timedelta(days=2)).dt.date.astype(str)
actions.append(("Corrected Ship Date earlier than Order Date", int(bad_mask.sum())))

# 4. Flag (not drop) rows with invalid Sales/Quantity/Discount so analysts can decide
df["DQ_Flag_InvalidSales"] = df["Sales"] <= 0
df["DQ_Flag_InvalidQuantity"] = (df["Quantity"] < 1) | (df["Quantity"] > 20)
df["DQ_Flag_InvalidDiscount"] = (df["Discount"] < 0) | (df["Discount"] > 1)
actions.append(("Flagged rows with invalid Sales", int(df["DQ_Flag_InvalidSales"].sum())))
actions.append(("Flagged rows with invalid Quantity", int(df["DQ_Flag_InvalidQuantity"].sum())))
actions.append(("Flagged rows with invalid Discount", int(df["DQ_Flag_InvalidDiscount"].sum())))

# 5. Flag Category/Sub-Category and State/Region mismatches (needs human judgement to fix correctly)
valid_pairs = {
    "Furniture": {"Bookcases","Chairs","Furnishings","Tables"},
    "Office Supplies": {"Appliances","Art","Binders","Envelopes","Fasteners","Labels","Paper","Storage","Supplies"},
    "Technology": {"Accessories","Copiers","Machines","Phones"},
}
df["DQ_Flag_CategoryMismatch"] = ~df.apply(lambda r: r["Sub-Category"] in valid_pairs.get(r["Category"], set()), axis=1)
actions.append(("Flagged Category/Sub-Category mismatches", int(df["DQ_Flag_CategoryMismatch"].sum())))

state_region = {
    "California":"West","Washington":"West","Oregon":"West","Arizona":"West",
    "Texas":"Central","Illinois":"Central","Ohio":"Central","Michigan":"Central",
    "Florida":"South","Georgia":"South","North Carolina":"South","Virginia":"South",
    "New York":"East","Pennsylvania":"East","New Jersey":"East","Massachusetts":"East",
}
def region_bad(state, region):
    if pd.isna(region) or state not in state_region: return False
    return state_region[state] != region
df["DQ_Flag_RegionMismatch"] = df.apply(lambda r: region_bad(r["State"], r["Region"]), axis=1)
actions.append(("Flagged State/Region mismatches", int(df["DQ_Flag_RegionMismatch"].sum())))

# 6. Missing-value flags (left as null, not imputed, so they stay visible)
for col in ["Customer Name","Postal Code","Region","Ship Date"]:
    df[f"DQ_Flag_Missing_{col.replace(' ','')}"] = df[col].isna()

n_after = len(df)
for a, c in actions:
    print(f"{a}: {c}")
print("Rows before:", n_before, "Rows after:", n_after)

df.to_csv("/mnt/user-data/outputs/superstore_cleaned_full.csv", index=False)
# a readable sample for the report / deliverable
sample = df.sort_values("Order ID").head(60)
sample.to_csv("/mnt/user-data/outputs/cleaned_sample.csv", index=False)

import json
json.dump([{"action":a,"count":c} for a,c in actions]+[{"rows_before":n_before,"rows_after":n_after}],
           open("clean_actions.json","w"))
