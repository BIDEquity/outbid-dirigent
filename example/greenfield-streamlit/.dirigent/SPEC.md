# CSV Data Explorer

Build a Streamlit app that lets a user upload a CSV file, explore its contents, and see basic statistics.

## Requirements

- Upload a CSV file via file uploader
- Display the raw data as a table
- Show basic statistics (row count, column count, dtypes)
- Show a bar chart of the first numeric column grouped by the first categorical column
- Handle edge cases: empty file, no numeric columns, no categorical columns

## Acceptance Criteria

- App starts with `./start.sh` and is accessible on port 8501
- Uploading `data/sample.csv` shows a table with all rows
- Statistics panel shows correct row/column counts
- Bar chart renders without errors when sample.csv is uploaded
- Empty CSV upload shows a user-friendly message, not a traceback

## Out of Scope

- Authentication
- Database storage
- Multi-file upload
- Export/download features
