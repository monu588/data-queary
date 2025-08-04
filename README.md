# Data Query Analytics Dashboard

AI-powered analytics dashboard that converts natural language queries into data visualizations.

## Features

- **Natural Language Queries**: Ask questions like "show sales by region" or "total sales in July"
- **Interactive Charts**: Automatic chart generation using Chart.js
- **Local Processing**: Works without external APIs using built-in query parser
- **Real-time Analysis**: Instant data processing and visualization
- **Responsive Design**: Modern dark theme with Bootstrap

## Files Structure

```
data_query/
├── app.py              # Main Flask application
├── main.py             # Entry point for Gunicorn
├── run.py              # Development server launcher
├── openai_service.py   # Query processing (local + OpenAI fallback)
├── sales.csv           # Sample sales dataset
├── templates/
│   └── index.html      # Frontend dashboard
├── static/
│   └── script.js       # Frontend JavaScript
└── README.md           # This file
```

## How to Use

1. Open the dashboard in your browser
2. Type natural language questions about your sales data
3. View results as interactive charts or data tables
4. Use sample queries for common analytics patterns

## Sample Queries

- "Show total sales by region"
- "Sales trends by month in 2023"
- "Top 5 highest sales days"
- "Average daily sales by region"
- "Sales in July"
- "Total sales"

## Technical Details

- **Backend**: Flask with pandas for data processing
- **Frontend**: Bootstrap 5 with Chart.js for visualizations
- **Data**: CSV-based with 365+ sales records
- **Query Processing**: Local pattern matching with OpenAI fallback
- **Security**: Code sandboxing for safe execution