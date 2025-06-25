# Data Directory

This directory contains sample data files for testing and demonstration purposes.

## Files

- `legal_spend_sample.csv` - Sample legal spend data with 15 invoices from various vendors
- Place your own CSV or Excel files here for testing

## Data Format

The CSV files should include the following columns:
- invoice_id
- vendor_name
- vendor_type
- matter_id
- matter_name
- department
- practice_area
- invoice_date
- amount
- currency
- expense_category
- description
- billing_period_start (optional)
- billing_period_end (optional)
- status
- budget_code (optional)

## Security Note

⚠️ **Never commit real/sensitive data to version control!**

Add any real data files to `.gitignore` to prevent accidental commits.