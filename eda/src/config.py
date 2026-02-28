from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Paths:
    eda_root: Path
    data_raw: Path
    data_processed: Path
    outputs_figures: Path
    outputs_tables: Path

@dataclass(frozen=True)
class Settings:
    paths: Paths
    min_pair_support_customers: int = 6
    exclude_charge_keywords: tuple = ("DELIVERY CHARGE", "SERVICE", "CHARGE")
    coffee_keywords: tuple = ("COFFEE", "ESPRESSO", "LATTE", "CAPPUCCINO", "MOCHA", "AMERICANO", "FLAT WHITE")
    milkshake_keywords: tuple = ("MILKSHAKE",)

def load_settings(eda_root: Path) -> Settings:
    """
    eda_root must be: .../503NHackathon/eda
    """
    paths = Paths(
        eda_root=eda_root,
        data_raw=eda_root / "data" / "raw",
        data_processed=eda_root / "data" / "processed",
        outputs_figures=eda_root / "outputs" / "figures",
        outputs_tables=eda_root / "outputs" / "tables",
    )

    # Ensure folders exist
    paths.data_processed.mkdir(parents=True, exist_ok=True)
    paths.outputs_figures.mkdir(parents=True, exist_ok=True)
    paths.outputs_tables.mkdir(parents=True, exist_ok=True)

    return Settings(paths=paths)