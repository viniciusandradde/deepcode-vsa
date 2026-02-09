
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from core.reports.excel import generate_cost_center_report_excel

async def test_report():
    print("Generating Excel report...")
    try:
        excel_bytes, filename = await generate_cost_center_report_excel()
        print(f"Success! Generated {len(excel_bytes)} bytes.")
        print(f"Filename: {filename}")
        
        # Save locally to inspect
        with open("test_report.xlsx", "wb") as f:
            f.write(excel_bytes)
        print("Saved to test_report.xlsx")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_report())
