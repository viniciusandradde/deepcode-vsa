
import os
import sys
from langsmith import Client

# Load env if needed, or rely on environment variables being set in the shell
from dotenv import load_dotenv
load_dotenv()

def fetch_run(run_id):
    client = Client()
    try:
        run = client.read_run(run_id)
        print(f"--- Run: {run.id} ---")
        print(f"Name: {run.name}")
        print(f"Type: {run.run_type}")
        print(f"Inputs: {run.inputs}")
        print(f"Outputs: {run.outputs}")
        print(f"Error: {run.error}")
        
        # If it has child runs (tool calls), we might want to see them
        # Note: read_run doesn't fetch children deep by default in all views, 
        # but let's check basic info first.
        
    except Exception as e:
        print(f"Error fetching run: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_trace.py <run_id>")
        sys.exit(1)
    
    run_id = sys.argv[1]
    fetch_run(run_id)
