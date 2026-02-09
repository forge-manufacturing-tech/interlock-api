import pandas as pd
import io

def parse_messy_bom(file_content: bytes, filename: str) -> list[dict]:
    """Parses an uploaded Excel/CSV BOM into a clean list of dicts"""
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_content))
    else:
        df = pd.read_excel(io.BytesIO(file_content))
    
    # "AI" Logic: rudimentary cleaning
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df.to_dict(orient="records")