"""Per-report ingestion parsers for Conut bakery report-style CSVs.

Each report has a unique layout with page headers, section markers, and sub-totals.
Every parser returns a clean pandas DataFrame ready for downstream processing.

NOTE: All parsers use csv.reader for correct handling of quoted comma-formatted
numerics (e.g. "1,137,352,241.41" must not be split on the internal commas).
"""

import csv
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


def _is_page_header(parts: list[str]) -> bool:
    """Detect report page-break header lines from a parsed row."""
    raw = ",".join(parts)
    return bool(re.search(r"Page \d+ of", raw))


def _is_copyright(parts: list[str]) -> bool:
    raw = ",".join(parts)
    return "Copyright" in raw or "omegapos" in raw.lower() or parts[0].startswith("REP_S_") or parts[0].startswith("rep_s_")


def _read_csv_rows(path: Path) -> list[list[str]]:
    """Read file using csv.reader, returning list of stripped-field rows."""
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            rows.append([p.strip() for p in row])
    return rows


# ---------------------------------------------------------------------------
# 1. REP_S_00136_SMRY  —  Summary By Division (sales by branch/category/channel)
# ---------------------------------------------------------------------------
def parse_division_summary(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["division_summary"]
    rows_out = []
    current_branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_page_header(parts) or _is_copyright(parts):
            continue
        raw0 = parts[0]

        if raw0.startswith("Summary By Division") or raw0.startswith("30-Jan-26"):
            continue

        # Column header rows
        flat = [p for p in parts if p]
        if flat == ["DELIVERY", "TABLE", "TAKE AWAY", "TOTAL"] or \
           flat[:4] == ["DELIVERY", "TABLE", "TAKE AWAY", "TOTAL"]:
            continue

        # Detect branch name
        candidate = raw0
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
                    rows_out.append({
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
            category = raw0 if raw0 else (parts[1] if len(parts) > 1 else "")
            if not category or category == "TOTAL":
                continue

            nums = []
            for p in parts[1:]:
                p_clean = p.replace(",", "").replace('"', "")
                if p_clean and re.match(r"^-?[\d]+\.?\d*$", p_clean):
                    nums.append(_parse_number(p))

            if len(nums) >= 4:
                rows_out.append({
                    "branch": current_branch,
                    "category": category,
                    "delivery": nums[0],
                    "table": nums[1],
                    "take_away": nums[2],
                    "total": nums[3],
                })
            elif len(nums) >= 1:
                rows_out.append({
                    "branch": current_branch,
                    "category": category,
                    "delivery": nums[0] if len(nums) > 0 else 0.0,
                    "table": nums[1] if len(nums) > 1 else 0.0,
                    "take_away": nums[2] if len(nums) > 2 else 0.0,
                    "total": nums[3] if len(nums) > 3 else 0.0,
                })

    df = pd.DataFrame(rows_out)
    log.info(f"Parsed division_summary: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2. REP_S_00194_SMRY  —  Tax Report (branch-level tax summary)
# ---------------------------------------------------------------------------
def parse_tax_summary(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["tax_summary"]
    rows_out = []
    branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_page_header(parts) or _is_copyright(parts):
            continue
        raw0 = parts[0]

        if "Tax Report" in raw0 or "Year:" in raw0:
            continue
        if raw0.startswith("TAX DESCRIPTION"):
            continue
        if raw0 in ("Conut - Tyre",) and not any(parts[1:]):
            continue  # Report title line

        if raw0.startswith("Branch Name:"):
            branch = raw0.replace("Branch Name:", "").strip()
            continue

        if raw0 == "Total By Branch":
            vat = _parse_number(parts[1]) if len(parts) > 1 else 0.0
            total = _parse_number(parts[-2]) if len(parts) > 2 else vat
            rows_out.append({
                "branch": branch,
                "vat_11_pct": vat,
                "total_tax": total,
            })

    df = pd.DataFrame(rows_out)
    log.info(f"Parsed tax_summary: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 3. REP_S_00461  —  Time & Attendance (punch in/out per employee)
# ---------------------------------------------------------------------------
def parse_attendance(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["attendance"]
    rows_out = []
    current_emp_id = None
    current_emp_name = None
    current_branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_copyright(parts):
            continue
        if _is_page_header(parts):
            continue

        raw0 = parts[0]

        if "Time & Attendance" in raw0 or raw0 in ("Conut - Tyre",):
            continue
        if "PUNCH IN" in raw0 or "PUNCH IN" in ",".join(parts):
            continue
        if "From Date:" in ",".join(parts) and "30-Jan-26" in parts[0]:
            continue

        # Employee header: ,EMP ID :X,NAME :PersonXXXX,,
        if len(parts) > 2 and "EMP ID" in parts[1]:
            emp_match = re.search(r"EMP ID\s*:\s*([\d.]+)", parts[1])
            name_match = re.search(r"NAME\s*:\s*(\S+)", parts[2])
            current_emp_id = emp_match.group(1) if emp_match else None
            current_emp_name = name_match.group(1) if name_match else None
            continue

        # Branch line: ,Branch Name,,,,
        if raw0 == "" and len(parts) >= 2 and parts[1] in (
            "Main Street Coffee", "Conut - Tyre", "Conut Jnah", "Conut"
        ):
            current_branch = parts[1]
            continue

        # Total row
        if "Total :" in ",".join(parts):
            continue

        # Data row: date,,punch_in_time,date,,punch_out_time,duration
        date_match = re.match(r"(\d{2}-\w{3}-\d{2})", raw0) if raw0 else None
        if date_match and current_emp_id:
            punch_in_date = raw0
            punch_in_time = parts[2] if len(parts) > 2 else ""
            punch_out_date = parts[3] if len(parts) > 3 else ""
            punch_out_time = parts[4] if len(parts) > 4 else ""
            duration = parts[5] if len(parts) > 5 else ""

            rows_out.append({
                "emp_id": current_emp_id,
                "emp_name": current_emp_name,
                "branch": current_branch,
                "punch_in_date": punch_in_date,
                "punch_in_time": punch_in_time.replace(".", ":"),
                "punch_out_date": punch_out_date,
                "punch_out_time": punch_out_time.replace(".", ":"),
                "duration_str": duration,
            })

    df = pd.DataFrame(rows_out)

    def _dur_to_hours(d: str) -> float:
        if not d:
            return 0.0
        d = d.replace(".", ":")
        p = d.split(":")
        try:
            h, m, s = float(p[0]), float(p[1]), float(p[2])
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
    rows_out = []
    current_customer = None
    current_branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_copyright(parts):
            continue
        if _is_page_header(parts):
            continue

        raw0 = parts[0]

        if raw0.startswith("Sales by customer"):
            continue
        if raw0.startswith("Full Name"):
            continue

        # Branch marker: "Branch :BranchName,,,,"
        if raw0.startswith("Branch :"):
            current_branch = raw0.replace("Branch :", "").strip()
            continue

        # Total Branch row
        if raw0.startswith("Total Branch:"):
            continue

        # Customer header: "Person_XXXX,,,," or "C_XXXX,..." etc.
        if re.match(r"^(Person_\d+|C_\d+)$", raw0):
            current_customer = raw0
            continue

        # Customer total: "Total :,qty,,price,"
        if raw0 == "Total :":
            continue

        # Item row: starts with empty first field
        if raw0 == "" and len(parts) >= 4:
            qty_str = parts[1]
            # Description is parts[2], price is parts[3]
            # (csv.reader handles quoted commas in description and price correctly)
            desc = parts[2].strip() if len(parts) > 2 else ""
            price_str = parts[3] if len(parts) > 3 else ""

            qty = _parse_number(qty_str)
            price = _parse_number(price_str)

            rows_out.append({
                "branch": current_branch,
                "customer": current_customer,
                "qty": qty,
                "description": desc,
                "price": price,
            })

    df = pd.DataFrame(rows_out)
    log.info(f"Parsed sales_detail: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 5. rep_s_00150  —  Customer Orders (delivery summary per customer)
# ---------------------------------------------------------------------------
def parse_customer_orders(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["customer_orders"]
    rows_out = []
    current_branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_copyright(parts):
            continue
        if _is_page_header(parts):
            continue

        raw0 = parts[0]

        # Skip report-level headers
        if raw0.startswith("Customer Orders"):
            continue
        if raw0.startswith("Customer Name"):
            continue

        # Branch section header: "BranchName,,,,,,,,,,"
        # Detected when parts[0] is a known branch name and the rest are empty
        name = raw0
        if name in ("Conut - Tyre", "Conut Jnah", "Main Street Coffee", "Conut"):
            rest = [p for p in parts[1:] if p]
            if not rest:
                current_branch = name
                continue

        if name.startswith("Total By Branch") or name.startswith("Total by Branch"):
            continue

        # Total row with leading empty cells: ",,Total By Branch,..."
        if raw0 == "" and len(parts) > 2 and parts[2].startswith("Total By Branch"):
            continue

        # Data row: Person_XXXX,address,phone,first_order,,last_order,,total,num_orders,
        if name.startswith("Person_"):
            address = parts[1] if len(parts) > 1 else ""
            phone = parts[2] if len(parts) > 2 else ""
            first_order = parts[3] if len(parts) > 3 else ""
            # Skip blank col (index 4)
            last_order = parts[5] if len(parts) > 5 else ""
            # Skip blank col (index 6)
            total = _parse_number(parts[7]) if len(parts) > 7 else 0.0
            num_orders = _parse_number(parts[8]) if len(parts) > 8 else 0.0

            rows_out.append({
                "branch": current_branch,
                "customer": name,
                "phone": phone,
                "first_order": first_order.rstrip(":"),
                "last_order": last_order.rstrip(":"),
                "total": total,
                "num_orders": int(num_orders),
            })

    df = pd.DataFrame(rows_out)
    log.info(f"Parsed customer_orders: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 6. rep_s_00191_SMRY  —  Sales by Items By Group
# ---------------------------------------------------------------------------
def parse_item_sales(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["item_sales"]
    rows_out = []
    current_branch = None
    current_division = None
    current_group = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_copyright(parts):
            continue
        if _is_page_header(parts):
            continue

        raw0 = parts[0]

        if raw0.startswith("Sales by Items"):
            continue
        if raw0.startswith("Description"):
            continue

        # Branch header
        if raw0.startswith("Branch:"):
            current_branch = raw0.replace("Branch:", "").strip()
            continue
        if raw0.startswith("Total by Branch:"):
            continue

        # Division header
        if raw0.startswith("Division:"):
            current_division = raw0.replace("Division:", "").strip()
            continue
        if raw0.startswith("Total by Division:"):
            continue

        # Group header
        if raw0.startswith("Group:"):
            current_group = raw0.replace("Group:", "").strip()
            continue
        if raw0.startswith("Total by Group:"):
            continue

        # Item row: description, barcode, qty, total_amount
        desc = raw0
        if not desc:
            continue

        # Find qty and total from remaining parts (csv.reader already stripped quotes)
        nums = []
        barcode = ""
        for p in parts[1:]:
            p_clean = p.replace(",", "")
            if p_clean and re.match(r"^-?\d+\.?\d*$", p_clean):
                nums.append(_parse_number(p))
            elif p and not barcode:
                barcode = p

        qty = nums[0] if len(nums) > 0 else 0.0
        total_amount = nums[1] if len(nums) > 1 else 0.0

        rows_out.append({
            "branch": current_branch or "Conut - Tyre",
            "division": current_division,
            "group": current_group,
            "description": desc,
            "barcode": barcode,
            "qty": qty,
            "total_amount": total_amount,
        })

    df = pd.DataFrame(rows_out)
    log.info(f"Parsed item_sales: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 7. rep_s_00334_1_SMRY  —  Monthly Sales by Branch
# ---------------------------------------------------------------------------
def parse_monthly_sales(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["monthly_sales"]
    rows_out = []
    current_branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_copyright(parts) or _is_page_header(parts):
            continue

        raw0 = parts[0]

        if "Monthly Sales" in raw0 or raw0.startswith("30-Jan-26"):
            continue
        if raw0.startswith("Month"):
            continue

        # Branch header
        if raw0.startswith("Branch Name:"):
            current_branch = raw0.replace("Branch Name:", "").strip()
            continue

        # Total/Grand Total
        if "Total" in raw0 or "Grand Total" in ",".join(parts):
            continue

        # Data row: month,,year,total,
        month_name = raw0
        if month_name in (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ):
            # csv.reader already handles quoted fields: parts[3] = "554,074,782.88" (unquoted)
            year = parts[2] if len(parts) > 2 else "2025"
            total = _parse_number(parts[3]) if len(parts) > 3 else 0.0
            rows_out.append({
                "branch": current_branch,
                "month": month_name,
                "year": int(year) if year.isdigit() else 2025,
                "total": total,
            })

    df = pd.DataFrame(rows_out)
    log.info(f"Parsed monthly_sales: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 8. rep_s_00435_SMRY  —  Average Sales By Menu
# ---------------------------------------------------------------------------
def parse_avg_menu_sales(path: Path | None = None) -> pd.DataFrame:
    path = path or FILES["avg_menu_sales"]
    rows_out = []
    current_branch = None

    for parts in _read_csv_rows(path):
        if not any(parts):
            continue
        if _is_copyright(parts) or _is_page_header(parts):
            continue

        raw0 = parts[0]

        if "Average Sales" in raw0 or raw0.startswith("30-Jan-26"):
            continue
        if raw0.startswith("Menu Name"):
            continue

        # Branch header
        name = raw0
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
            rows_out.append({
                "branch": current_branch,
                "menu_type": name,
                "num_customers": int(num_cust),
                "sales": sales,
                "avg_customer": avg_customer,
            })

    df = pd.DataFrame(rows_out)
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
