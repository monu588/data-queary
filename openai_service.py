import json
import os
import re
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def parse_query_locally(query, columns):
    """
    Local query parser that converts natural language to pandas code.
    Works without external API dependencies.
    """
    query_lower = query.lower().strip()
    
    # Common query patterns and their pandas code
    patterns = [
        # Sales by region
        {
            'keywords': ['sales', 'by', 'region'],
            'code': 'result = df.groupby("region")["sales"].sum().reset_index()',
            'description': 'Total sales by region'
        },
        # Sales by month
        {
            'keywords': ['sales', 'month', 'by'],
            'code': 'result = df.groupby(df["date"].dt.to_period("M"))["sales"].sum().reset_index()\nresult["date"] = result["date"].astype(str)',
            'description': 'Sales by month'
        },
        # Average sales by region
        {
            'keywords': ['average', 'sales', 'region'],
            'code': 'result = df.groupby("region")["sales"].mean().reset_index()',
            'description': 'Average sales by region'
        },
        # Top/highest sales
        {
            'keywords': ['top', 'highest', 'sales'],
            'code': 'result = df.nlargest(10, "sales")[["date", "region", "sales"]]',
            'description': 'Top 10 highest sales'
        },
        # Sales in specific month (July)
        {
            'keywords': ['sales', 'july'],
            'code': 'result = df[df["date"].dt.month == 7]',
            'description': 'Sales in July'
        },
        # Sales in specific year
        {
            'keywords': ['sales', '2023'],
            'code': 'result = df[df["date"].dt.year == 2023]',
            'description': 'Sales in 2023'
        },
        # Total sales
        {
            'keywords': ['total', 'sales'],
            'code': 'result = df["sales"].sum()',
            'description': 'Total sales'
        },
        # Sales trends
        {
            'keywords': ['trend', 'sales'],
            'code': 'result = df.groupby(df["date"].dt.to_period("M"))["sales"].sum().reset_index()\nresult["date"] = result["date"].astype(str)',
            'description': 'Sales trends over time'
        },
        # Count of records
        {
            'keywords': ['count', 'records'],
            'code': 'result = len(df)',
            'description': 'Total number of records'
        },
        # Average daily sales
        {
            'keywords': ['average', 'daily', 'sales'],
            'code': 'result = df.groupby("date")["sales"].sum().mean()',
            'description': 'Average daily sales'
        }
    ]
    
    # Find best matching pattern
    best_match = None
    max_matches = 0
    
    for pattern in patterns:
        matches = sum(1 for keyword in pattern['keywords'] if keyword in query_lower)
        if matches > max_matches and matches > 0:
            max_matches = matches
            best_match = pattern
    
    if best_match:
        return best_match['code'], None
    
    # Default fallback - show basic dataset info
    return 'result = df.head(10)', None

def generate_pandas_code(query, columns):
    """
    Convert natural language query into pandas code.
    Uses OpenAI GPT-4o if available, otherwise falls back to local parser.
    Returns the generated code and any error message.
    """
    # If OpenAI API is not available, use local parser
    if not openai or not OPENAI_API_KEY:
        return parse_query_locally(query, columns)
    
    try:
        system_prompt = f"""You are an expert data analyst. Convert natural language queries into pandas code.

Dataset information:
- DataFrame name: df
- Columns: {columns}
- The 'date' column is already parsed as datetime
- Always assign your final result to a variable named 'result'

Rules:
1. Only use pandas operations and standard Python
2. Do not import any modules (pandas is available as 'pd')
3. The dataframe is available as 'df'
4. For date operations, the 'date' column is already datetime type
5. Always assign final output to 'result' variable
6. For aggregations, return DataFrames when possible for better visualization
7. Use descriptive column names in results
8. For time-based queries, extract relevant date components (month, year, etc.)

Examples:
Query: "total sales by region"
Code: result = df.groupby('region')['sales'].sum().reset_index()

Query: "sales in July 2023"  
Code: result = df[(df['date'].dt.year == 2023) & (df['date'].dt.month == 7)]

Query: "average sales per month"
Code: result = df.groupby(df['date'].dt.to_period('M'))['sales'].mean().reset_index()
result['date'] = result['date'].astype(str)

Respond with JSON containing the pandas code:
{{"code": "pandas code here"}}
"""
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate pandas code for: {query}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        if content is None:
            return None, "OpenAI response content is empty"
        result = json.loads(content)
        
        if 'code' not in result:
            return None, "OpenAI response does not contain 'code' field"
        
        return result['code'], None
        
    except Exception as e:
        # Fallback to local parser if OpenAI fails
        return parse_query_locally(query, columns)
