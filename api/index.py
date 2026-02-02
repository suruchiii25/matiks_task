import json
import sys
import os
from pathlib import Path

# Add the root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Import the aggregator
        from aggregator import run_once, setup_logging
        import pandas as pd
        
        # Set up output directory
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Run the aggregation
        logger = setup_logging(str(output_dir))
        df = run_once(query="Matiks", output_dir=str(output_dir), limit=20, logger=logger)
        
        # Read the dashboard HTML
        dashboard_path = output_dir / "dashboard.html"
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                dashboard_html = f.read()
        else:
            dashboard_html = "<h1>Dashboard not found. Please run the aggregator first.</h1>"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            },
            'body': dashboard_html
        }
        
    except Exception as e:
        import traceback
        error_html = f"""
        <h1>Error</h1>
        <p>Failed to generate dashboard: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': error_html
        }
