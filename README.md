# Data Quality Audit: Superstore Dataset

A repeatable data quality audit of a Superstore-style retail sales dataset, built in Python and Pandas.

## Objective
Audit the dataset for missing values, duplicates, out-of-range values and consistency issues, using a fixed checklist of validation rules that can be re-run on any future data load.

## Tools
- Python
- Pandas

## Dataset
A synthetic Superstore-style order dataset (610 rows, 20 columns: order, customer, geography and financial fields), generated with deliberately realistic data quality problems so the audit has something real to find.

## Files
| File | Purpose |
|------|---------|
| `generate_dataset.py` | Builds the raw dataset (not required to re-run the audit; included for transparency) |
| `superstore_raw.csv` | The raw, unaudited dataset |
| `audit.py` | Runs the 9 validation rules and writes `issue_log.csv` |
| `issue_log.csv` | **Issue log deliverable** — every issue found, with row, column, type and description |
| `clean.py` | Cleans/flags the data based on the audit and writes the cleaned files |
| `cleaned_sample.csv` | **Cleaned sample deliverable** — 60-row sample of the cleaned, flagged data |
| `superstore_cleaned_full.csv` | Full cleaned dataset (all 603 rows after dedup) |
| `data_quality_audit_report.docx` | **Audit report deliverable** — rules, results, cleaning actions, insights |
| `README.md` | This file |

## How to run
```bash
pip install pandas numpy
python generate_dataset.py   # optional: regenerate the raw data
python audit.py              # produces issue_log.csv
python clean.py              # produces cleaned_sample.csv and the full cleaned file
```

## Validation rules
| # | Rule | Category |
|---|------|----------|
| R1 | Customer Name, Postal Code, Region, Ship Date must not be missing | Completeness |
| R2 | No exact duplicate rows | Uniqueness |
| R3 | Sales must be greater than 0 | Validity (range) |
| R4 | Quantity must be between 1 and 20 | Validity (range) |
| R5 | Discount must be between 0 and 1 | Validity (range) |
| R6 | Ship Date must be on/after Order Date | Consistency |
| R7 | Sub-Category must belong to the stated Category | Consistency |
| R8 | Region must match the State-to-Region reference mapping | Consistency |
| R9 | State/City text must be trimmed and consistently cased | Formatting |

## Results summary
- 103 issues found across 97 distinct rows (15.9% of the dataset)
- Missing values are the largest category (35), concentrated in Customer Name, Postal Code and Region
- 7 exact duplicate rows removed; formatting, date-order and reference-mapping issues flagged or corrected

## Key insights
- Missing required fields should be enforced at data-entry time, not caught after the fact.
- Category/Sub-Category and State/Region mismatches suggest free-text entry where a constrained lookup should be used.
- Discount values over 100% point to a likely percentage/decimal entry error.

## Next steps
Enforce these same rules at the point of data entry (dropdowns, required fields) so issues don't recur, and schedule `audit.py` to run automatically on every new data load.
