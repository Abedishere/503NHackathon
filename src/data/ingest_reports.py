"""Per-report ingestion parsers for Conut bakery report-style CSVs.

Each report has a unique layout with page headers, section markers, and sub-totals.
Every parser returns a clean pandas DataFrame ready for downstream processing.
"""

import re
import pandas as pd
from pathlib import Path
from src.config import FILES
from src.utils.logging import get_logger

log = get_logger(__name__)


def _parse_number(val: str) -> float:
    """Parse a comma-formatted number string into a float."""
    if not val or not isinstance(val, str):
        return 0.0
    val = val.strip().strip('"')
    val = val.replace(",", "")
    try:
        return float(val)
    except ValueError:
        return 0.0


def _is_page_header(line: str) -> bool:
    """Detect report page-break header lines."""
    return bool(re.search(r"Page \d+ of", line))


def _is_copyright(line: str) -> bool:
    return "Copyright" in line or "omegapos" in line.lower() or line.startswith("REP_S_") or line.startswith("rep_s_")


# ---------------------------------------------------------------------------
# 1. REP_S_00136_SMRY  —  Summary By Division (sales by branch/category/channel)
# ---------------------------------------------------------------------------
def parse_division_summary(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["division_summary"]
    rows = []
    current_branch = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or _is_page_header(line) or _is_copyright(line):
            continue
        if line.startswith("Conut - Tyre,") and "Summary" in line:
            continue
        if line.startswith("Summary By Division") or line.startswith("30-Jan-26"):
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]

        # Column header rows
        if parts == ["", "DELIVERY", "TABLE", "TAKE AWAY", "TOTAL"] or \
           parts[:4] == ["DELIVERY", "TABLE", "TAKE AWAY", "TOTAL"]:
            continue

        # Detect branch name (first column is non-empty and is a known branch)
        if parts[0] and parts[0] not in ("", "TOTAL") and not parts[0].startswith(","):
            # Could be branch header or branch + category row
            candidate = parts[0].strip()
            if candidate in ("Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"):
                current_branch = candidate
                # Check if this line also has category data
                if len(parts) > 1 and parts[1]:
                    category = parts[1]
                    delivery = _parse_number(parts[2]) if len(parts) > 2 else 0.0
                    table = _parse_number(parts[3]) if len(parts) > 3 else 0.0
                    take_away = _parse_number(parts[4]) if len(parts) > 4 else 0.0
                    total = _parse_number(parts[5]) if len(parts) > 5 else 0.0
                    if category != "TOTAL":
                        rows.append({
                            "branch": current_branch,
                            "category": category,
                            "delivery": delivery,
                            "table": table,
                            "take_away": take_away,
                            "total": total,
                        })
                continue

        # Category row (branch is empty, first non-empty is category)
        if current_branch and len(parts) > 1:
            category = parts[0] if parts[0] else (parts[1] if len(parts) > 1 else "")
            if not category or category == "TOTAL":
                continue

            # Find numeric columns — depends on which layout section
            # Layout A (first section): col0=branch, col1=category, col2=delivery, col3=table, col4=take_away, col5=total
            # Layout B (later): col0=branch, col1=category, col2=delivery, col3=table, col4=take_away, col5=total
            nums = []
            for p in parts[1:]:
                if p and re.match(r"^-?[\d,]+\.?\d*$", p.replace('"', '').replace(',', '')):
                    nums.append(_parse_number(p))

            if len(nums) >= 4:
                rows.append({
                    "branch": current_branch,
                    "category": category,
                    "delivery": nums[0],
                    "table": nums[1],
                    "take_away": nums[2],
                    "total": nums[3],
                })
            elif len(nums) >= 1:
                rows.append({
                    "branch": current_branch,
                    "category": category,
                    "delivery": nums[0] if len(nums) > 0 else 0.0,
                    "table": nums[1] if len(nums) > 1 else 0.0,
                    "take_away": nums[2] if len(nums) > 2 else 0.0,
                    "total": nums[3] if len(nums) > 3 else 0.0,
                })

    df = pd.DataFrame(rows)
    log.info(f"Parsed division_summary: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2. REP_S_00194_SMRY  —  Tax Report (branch-level tax summary)
# ---------------------------------------------------------------------------
def parse_tax_summary(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["tax_summary"]
    rows = []

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or _is_page_header(line) or _is_copyright(line):
            continue
        if "Tax Report" in line or "Conut - Tyre" in line or "Year:" in line:
            continue
        if line.startswith("TAX DESCRIPTION"):
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]

        if parts[0].startswith("Branch Name:"):
            branch = parts[0].replace("Branch Name:", "").strip()
            continue

        if parts[0] == "Total By Branch":
            vat = _parse_number(parts[1]) if len(parts) > 1 else 0.0
            total = _parse_number(parts[-2]) if len(parts) > 2 else vat
            rows.append({
                "branch": branch,
                "vat_11_pct": vat,
                "total_tax": total,
            })

    df = pd.DataFrame(rows)
    log.info(f"Parsed tax_summary: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 3. REP_S_00461  —  Time & Attendance (punch in/out per employee)
# ---------------------------------------------------------------------------
def parse_attendance(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["attendance"]
    rows = []
    current_emp_id = None
    current_emp_name = None
    current_branch = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or _is_copyright(line):
            continue

        parts = [p.strip() for p in line.split(",")]

        # Page header
        if _is_page_header(line):
            continue
        if "Time & Attendance" in line or line == "Conut - Tyre":
            continue
        if "PUNCH IN" in line:
            continue
        if "From Date:" in line and "30-Jan-26" in line:
            continue

        # Employee header: ,EMP ID :X,NAME :PersonXXXX,,
        if len(parts) > 2 and "EMP ID" in parts[1]:
            emp_match = re.search(r"EMP ID\s*:\s*([\d.]+)", parts[1])
            name_match = re.search(r"NAME\s*:\s*(\S+)", parts[2])
            current_emp_id = emp_match.group(1) if emp_match else None
            current_emp_name = name_match.group(1) if name_match else None
            continue

        # Branch line: ,Branch Name,,,,
        if len(parts) >= 2 and parts[0] == "" and parts[1] in (
            "Main Street Coffee", "Conut - Tyre", "Conut Jnah", "Conut"
        ):
            current_branch = parts[1]
            continue

        # Total row
        if "Total :" in line:
            continue

        # Data row: date,,punch_in_time,date,,punch_out_time,duration
        date_match = re.match(r"(\d{2}-\w{3}-\d{2})", parts[0]) if parts else None
        if date_match and current_emp_id:
            punch_in_date = parts[0]
            punch_in_time = parts[2] if len(parts) > 2 else ""
            punch_out_date = parts[3] if len(parts) > 3 else ""
            punch_out_time = parts[4] if len(parts) > 4 else ""
            duration = parts[5] if len(parts) > 5 else ""

            rows.append({
                "emp_id": current_emp_id,
                "emp_name": current_emp_name,
                "branch": current_branch,
                "punch_in_date": punch_in_date,
                "punch_in_time": punch_in_time.replace(".", ":"),
                "punch_out_date": punch_out_date,
                "punch_out_time": punch_out_time.replace(".", ":"),
                "duration_str": duration,
            })

    df = pd.DataFrame(rows)
    # Parse duration into hours
    def _dur_to_hours(d: str) -> float:
        if not d:
            return 0.0
        # Format can be HH:MM:SS or HH.MM.SS or H:MM:SS
        d = d.replace(".", ":")
        parts = d.split(":")
        try:
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return h + m / 60.0 + s / 3600.0
        except (ValueError, IndexError):
            return 0.0

    if not df.empty:
        df["hours_worked"] = df["duration_str"].apply(_dur_to_hours)

    log.info(f"Parsed attendance: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 4. REP_S_00502  —  Sales by customer in details (line-item transactions)
# ---------------------------------------------------------------------------
def parse_sales_detail(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["sales_detail"]
    rows = []
    current_customer = None
    current_branch = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        raw = line.strip()
        if not raw or _is_copyright(raw):
            continue
        if _is_page_header(raw):
            continue
        if raw.startswith("Sales by customer") or raw == "Conut - Tyre,,,,":
            continue
        if raw.startswith("Full Name,"):
            continue

        parts = [p.strip() for p in line.split(",")]

        # Branch marker: "Branch :BranchName,,,,"
        if parts[0].startswith("Branch :"):
            current_branch = parts[0].replace("Branch :", "").strip()
            continue

        # Total Branch row
        if parts[0].startswith("Total Branch:"):
            continue

        # Customer header: "Person_XXXX,,,,"
        if re.match(r"^Person_\d+$", parts[0]):
            current_customer = parts[0]
            continue

        # Customer total: "Total :,qty,,price,"
        if parts[0] == "Total :":
            continue

        # Item row: ",qty,  description,price,"
        if parts[0] == "" and len(parts) >= 4:
            qty_str = parts[1].strip()
            # Description may contain commas — reconstruct
            # The price is the last numeric field
            # Find the price (last field that looks numeric)
            price_str = ""
            desc_parts = []
            for i in range(2, len(parts)):
                val = parts[i].strip().strip('"')
                if val and re.match(r'^-?[\d,]+\.?\d*$', val.replace(",", "")):
                    price_str = val
                elif val:
                    desc_parts.append(val)

            desc = " ".join(desc_parts).strip()
            qty = _parse_number(qty_str)
            price = _parse_number(price_str)

            rows.append({
                "branch": current_branch,
                "customer": current_customer,
                "qty": qty,
                "description": desc,
                "price": price,
            })

    df = pd.DataFrame(rows)
    log.info(f"Parsed sales_detail: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 5. rep_s_00150  —  Customer Orders (delivery summary per customer)
# ---------------------------------------------------------------------------
def parse_customer_orders(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["customer_orders"]
    rows = []
    current_branch = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        raw = line.strip()
        if not raw or _is_copyright(raw):
            continue
        if _is_page_header(raw):
            continue
        if raw.startswith("Customer Orders") or raw.startswith("Conut - Tyre,"):
            continue
        if raw.startswith("Customer Name,"):
            continue

        parts = [p.strip() for p in line.split(",")]

        # Branch header (standalone)
        name = parts[0].strip()
        if name in ("Conut - Tyre", "Conut Jnah", "Main Street Coffee", "Conut"):
            # Check if it's just a branch header (rest is empty)
            rest = [p.strip() for p in parts[1:] if p.strip()]
            if not rest:
                current_branch = name
                continue

        if name.startswith("Total By Branch") or name.startswith("Total by Branch"):
            continue

        # Data row: name,address,phone,first_order,,last_order,,total,num_orders,
        if name.startswith("Person_"):
            address = parts[1].strip() if len(parts) > 1 else ""
            phone = parts[2].strip() if len(parts) > 2 else ""
            first_order = parts[3].strip() if len(parts) > 3 else ""
            # Skip blank col (index 4)
            last_order = parts[5].strip() if len(parts) > 5 else ""
            # Skip blank col (index 6)
            total = _parse_number(parts[7]) if len(parts) > 7 else 0.0
            num_orders = _parse_number(parts[8]) if len(parts) > 8 else 0.0

            rows.append({
                "branch": current_branch,
                "customer": name,
                "phone": phone,
                "first_order": first_order.rstrip(":"),
                "last_order": last_order.rstrip(":"),
                "total": total,
                "num_orders": int(num_orders),
            })

    df = pd.DataFrame(rows)
    log.info(f"Parsed customer_orders: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 6. rep_s_00191_SMRY  —  Sales by Items By Group
# ---------------------------------------------------------------------------
def parse_item_sales(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["item_sales"]
    rows = []
    current_branch = None
    current_division = None
    current_group = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        raw = line.strip()
        if not raw or _is_copyright(raw):
            continue
        if _is_page_header(raw):
            continue
        if raw.startswith("Sales by Items") or raw.startswith("Conut - Tyre,"):
            continue
        if raw.startswith("Description,Barcode"):
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]

        # Branch header
        if parts[0].startswith("Branch:"):
            current_branch = parts[0].replace("Branch:", "").strip()
            continue
        if parts[0].startswith("Total by Branch:"):
            branch_name = parts[0].replace("Total by Branch:", "").strip()
            continue

        # Division header
        if parts[0].startswith("Division:"):
            current_division = parts[0].replace("Division:", "").strip()
            continue
        if parts[0].startswith("Total by Division:"):
            continue

        # Group header
        if parts[0].startswith("Group:"):
            current_group = parts[0].replace("Group:", "").strip()
            continue
        if parts[0].startswith("Total by Group:"):
            continue

        # Item row: description, barcode, qty, total_amount
        desc = parts[0]
        if not desc:
            continue

        # Find qty and total from remaining parts
        nums = []
        barcode = ""
        for p in parts[1:]:
            p_clean = p.replace(",", "").replace('"', '')
            if re.match(r'^-?\d+\.?\d*$', p_clean) and p_clean:
                nums.append(_parse_number(p))
            elif p and not barcode:
                barcode = p

        qty = nums[0] if len(nums) > 0 else 0.0
        total_amount = nums[1] if len(nums) > 1 else 0.0

        rows.append({
            "branch": current_branch or "Conut - Tyre",
            "division": current_division,
            "group": current_group,
            "description": desc,
            "barcode": barcode,
            "qty": qty,
            "total_amount": total_amount,
        })

    df = pd.DataFrame(rows)
    log.info(f"Parsed item_sales: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 7. rep_s_00334_1_SMRY  —  Monthly Sales by Branch
# ---------------------------------------------------------------------------
def parse_monthly_sales(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["monthly_sales"]
    rows = []
    current_branch = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        raw = line.strip()
        if not raw or _is_copyright(raw) or _is_page_header(raw):
            continue
        if "Monthly Sales" in raw or raw == "Conut - Tyre,,,,":
            continue
        if raw.startswith("30-Jan-26"):
            continue
        if raw.startswith("Month,"):
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]

        # Branch header
        if parts[0].startswith("Branch Name:"):
            current_branch = parts[0].replace("Branch Name:", "").strip()
            continue

        # Total/Grand Total
        if "Total" in parts[0] or "Grand Total" in " ".join(parts):
            continue

        # Data row: month,,year,total,
        month_name = parts[0]
        if month_name in (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ):
            year = parts[2] if len(parts) > 2 else "2025"
            total = _parse_number(parts[3]) if len(parts) > 3 else 0.0
            rows.append({
                "branch": current_branch,
                "month": month_name,
                "year": int(year),
                "total": total,
            })

    df = pd.DataFrame(rows)
    log.info(f"Parsed monthly_sales: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 8. rep_s_00435_SMRY  —  Average Sales By Menu
# ---------------------------------------------------------------------------
def parse_avg_menu_sales(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["avg_menu_sales"]
    rows = []
    current_branch = None

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        raw = line.strip()
        if not raw or _is_copyright(raw) or _is_page_header(raw):
            continue
        if "Average Sales" in raw or raw.startswith("Conut - Tyre,") or raw.startswith("30-Jan-26"):
            continue
        if raw.startswith("Menu Name,"):
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]

        # Branch header
        name = parts[0]
        if name in ("Conut - Tyre", "Conut Jnah", "Main Street Coffee", "Conut"):
            rest = [p for p in parts[1:] if p]
            if not rest:
                current_branch = name
                continue

        if name.startswith("Total By Branch") or name.startswith("Total :"):
            continue

        # Data row: menu_name, num_cust, sales, avg_customer
        if name in ("DELIVERY", "TABLE", "TAKE AWAY"):
            num_cust = _parse_number(parts[1]) if len(parts) > 1 else 0.0
            sales = _parse_number(parts[2]) if len(parts) > 2 else 0.0
            avg_customer = _parse_number(parts[3]) if len(parts) > 3 else 0.0
            rows.append({
                "branch": current_branch,
                "menu_type": name,
                "num_customers": int(num_cust),
                "sales": sales,
                "avg_customer": avg_customer,
            })

    df = pd.DataFrame(rows)
    log.info(f"Parsed avg_menu_sales: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# Master ingestion: parse all reports
# ---------------------------------------------------------------------------
def ingest_all() -> dict[str, pd.DataFrame]:
    """Parse all 8 unique report files and return a dict of DataFrames."""
    return {
        "division_summary": parse_division_summary(),
        "tax_summary": parse_tax_summary(),
        "attendance": parse_attendance(),
        "sales_detail": parse_sales_detail(),
        "customer_orders": parse_customer_orders(),
        "item_sales": parse_item_sales(),
        "monthly_sales": parse_monthly_sales(),
        "avg_menu_sales": parse_avg_menu_sales(),
    }
