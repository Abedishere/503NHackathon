"""Central configuration for the Conut Operations Agent."""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "Conut bakery Scaled Data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
EDA_TABLES_DIR = PROJECT_ROOT / "eda" / "outputs" / "tables"
ARTIFACTS_DIR.mkdir(exist_ok=True)

# API settings
API_HOST = os.getenv("CONUT_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("CONUT_API_PORT", "8000"))

# OpenClaw integration settings (mandatory — skill-based + webhook)
OPENCLAW_GATEWAY_URL = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
OPENCLAW_HOOK_TOKEN = os.getenv("OPENCLAW_HOOK_TOKEN", "")

# Data file paths
FILES = {
    "division_summary": DATA_DIR / "REP_S_00136_SMRY.csv",
    "tax_summary": DATA_DIR / "REP_S_00194_SMRY.csv",
    "attendance": DATA_DIR / "REP_S_00461.csv",
    "sales_detail": DATA_DIR / "REP_S_00502.csv",
    "customer_orders": DATA_DIR / "rep_s_00150.csv",
    "item_sales": DATA_DIR / "rep_s_00191_SMRY.csv",
    "monthly_sales": DATA_DIR / "rep_s_00334_1_SMRY.csv",
    "avg_menu_sales": DATA_DIR / "rep_s_00435_SMRY.csv",
}
