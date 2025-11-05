# app/scripts/check_missing_logos.py
import pandas as pd
import os

LOGO_EXTENSIONS = [".png", ".gif", ".jpg", ".jpeg", ".bmp"]
LOGO_DIR = "static/logos"

def logo_exists(code: str) -> bool:
    for ext in LOGO_EXTENSIONS:
        for name_variant in [code, code.lower(), code.upper()]:
            if os.path.exists(os.path.join(LOGO_DIR, f"{name_variant}{ext}")):
                return True
    return False

def main():
    airlines_df = pd.read_excel("data/Airline Code.xlsx")
    missing = []
    for _, row in airlines_df.iterrows():
        code = str(row["AIRLINECODE"]).strip()
        if not logo_exists(code):
            missing.append(code)
    if missing:
        print(f"⚠️ Missing logos for {len(missing)} airlines:")
        print(", ".join(missing))
    else:
        print("✅ All airlines have logos!")

if __name__ == "__main__":
    main()
