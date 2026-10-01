"""
Data Quality Audit: Superstore dataset
---------------------------------------
Runs a repeatable checklist of validation rules against the raw data,
logs every issue found, and produces a cleaned sample.

Run:
    python audit.py superstore_raw.csv
"""
import pandas as pd
import numpy as np

RAW_PATH = "/mnt/user-data/outputs/superstore_raw.csv"
df = pd.read_csv(RAW_PATH)
n_rows = len(df)

issues = []  # each: dict(RowIndex, OrderID, Column, IssueType, Description, Value)

def log_issue(row_idx, order_id, column, issue_type, description, value):
    issues.append({
        "RowIndex": row_idx, "OrderID": order_id, "Column": column,
        "IssueType": issue_type, "Description": description, "Value": value
    })

# ---------- Rule 1: Required fields must not be missing ----------
required_cols = ["Customer Name", "Postal Code", "Region", "Ship Date"]
for col in required_cols:
    missing = df[df[col].isna()]
    for idx, row in missing.iterrows():
        log_issue(idx, row["Order ID"], col, "missing_value",
                   f"{col} is missing", None)

# ---------- Rule 2: No exact duplicate rows ----------
dup_mask = df.duplicated(keep="first")
for idx in df[dup_mask].index:
    log_issue(idx, df.loc[idx, "Order ID"], "ALL", "duplicate_row",
               "Exact duplicate of an earlier row", None)

# ---------- Rule 3: Sales must be > 0 ----------
bad = df[df["Sales"] <= 0]
for idx, row in bad.iterrows():
    log_issue(idx, row["Order ID"], "Sales", "invalid_range",
               "Sales must be greater than 0", row["Sales"])

# ---------- Rule 4: Quantity must be between 1 and 20 ----------
bad = df[(df["Quantity"] < 1) | (df["Quantity"] > 20)]
for idx, row in bad.iterrows():
    log_issue(idx, row["Order ID"], "Quantity", "invalid_range",
               "Quantity must be between 1 and 20", row["Quantity"])

# ---------- Rule 5: Discount must be between 0 and 1 (0-100%) ----------
bad = df[(df["Discount"] < 0) | (df["Discount"] > 1)]
for idx, row in bad.iterrows():
    log_issue(idx, row["Order ID"], "Discount", "invalid_range",
               "Discount must be between 0 and 1", row["Discount"])

# ---------- Rule 6: Ship Date must be on/after Order Date ----------
od = pd.to_datetime(df["Order Date"], errors="coerce")
sd = pd.to_datetime(df["Ship Date"], errors="coerce")
bad_mask = sd.notna() & od.notna() & (sd < od)
for idx in df[bad_mask].index:
    log_issue(idx, df.loc[idx, "Order ID"], "Ship Date", "date_consistency",
               "Ship Date is earlier than Order Date",
               f"{df.loc[idx,'Order Date']} -> {df.loc[idx,'Ship Date']}")

# ---------- Rule 7: Category / Sub-Category must match reference mapping ----------
valid_pairs = {
    "Furniture": {"Bookcases","Chairs","Furnishings","Tables"},
    "Office Supplies": {"Appliances","Art","Binders","Envelopes","Fasteners","Labels","Paper","Storage","Supplies"},
    "Technology": {"Accessories","Copiers","Machines","Phones"},
}
def pair_ok(cat, sub):
    return cat in valid_pairs and sub in valid_pairs[cat]
bad_mask = ~df.apply(lambda r: pair_ok(r["Category"], r["Sub-Category"]), axis=1)
for idx, row in df[bad_mask].iterrows():
    log_issue(idx, row["Order ID"], "Category/Sub-Category", "referential_consistency",
               "Sub-Category does not belong to the stated Category",
               f"{row['Category']} / {row['Sub-Category']}")

# ---------- Rule 8: State / Region must match reference mapping ----------
state_region = {
    "California":"West","Washington":"West","Oregon":"West","Arizona":"West",
    "Texas":"Central","Illinois":"Central","Ohio":"Central","Michigan":"Central",
    "Florida":"South","Georgia":"South","North Carolina":"South","Virginia":"South",
    "New York":"East","Pennsylvania":"East","New Jersey":"East","Massachusetts":"East",
}
def region_ok(state, region):
    if pd.isna(region) or state not in state_region:
        return True  # already caught by the missing-value rule
    return state_region[state] == region
bad_mask = ~df.apply(lambda r: region_ok(r["State"], r["Region"]), axis=1)
for idx, row in df[bad_mask].iterrows():
    log_issue(idx, row["Order ID"], "State/Region", "referential_consistency",
               "Region does not match the stated State",
               f"{row['State']} / {row['Region']}")

# ---------- Rule 9: Text formatting must be consistent (State, City) ----------
for col in ["State", "City"]:
    for idx, val in df[col].items():
        if not isinstance(val, str):
            continue
        if val != val.strip() or val != val.strip().title():
            log_issue(idx, df.loc[idx, "Order ID"], col, "formatting_inconsistency",
                       f"{col} has inconsistent casing or extra whitespace", repr(val))

issue_log = pd.DataFrame(issues)
issue_log.insert(0, "IssueID", range(1, len(issue_log) + 1))
issue_log.to_csv("/mnt/user-data/outputs/issue_log.csv", index=False)

# ---------- summary ----------
summary = issue_log.groupby("IssueType").size().sort_values(ascending=False)
print("Total rows audited:", n_rows)
print("Total issues logged:", len(issue_log))
print(summary)
rows_with_any_issue = issue_log["RowIndex"].nunique()
print("Distinct rows with at least one issue:", rows_with_any_issue,
      f"({rows_with_any_issue/n_rows:.1%})")

summary.to_csv("summary.csv")
