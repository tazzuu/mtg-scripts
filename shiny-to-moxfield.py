#!/usr/bin/env python3
import os
import re
import csv
import sys
import json
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

this_file_path = os.path.realpath(__file__)
this_dir_path = os.path.dirname(this_file_path)
default_sets_json = os.path.join(this_dir_path, "mtg_sets.json")
default_output_filename = "moxfield-converted-collection.csv"

# --- Output CSV schema ---------------------------------------------------------
MOXFIELD_FIELDS: List[str] = [
    "Count",
    "Tradelist Count",
    "Name",
    "Edition",
    "Condition",
    "Language",
    "Foil",
    "Tags",
    "Last Modified",
    "Collector Number",
    "Alter",
    "Proxy",
    "Purchase Price",
]

# --- Helpers -------------------------------------------------------------------
def _format_last_modified(date_str: str) -> str:
    if not date_str:
        return ""
    s = date_str.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        return date_str

def _collector_number(discriminator: str) -> str:
    return (discriminator or "").lstrip("#").strip()

def _edition_code(set_name: str, exact_map: Dict[str, str], ci_map: Dict[str, str]) -> str:
    name = (set_name or "").strip()
    if not name:
        return ""
    if name in exact_map:
        return exact_map[name]
    return ci_map.get(name.lower(), name)  # fallback to original set_name

def load_set_mapping(path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Load JSON mapping { "Set Name": "setcode", ... } from file.
    Returns (exact_map, case_insensitive_map).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: mapping file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: mapping file is not valid JSON: {path}\n{e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(raw, dict):
        print("ERROR: mapping JSON must be an object of {set_name: set_code}", file=sys.stderr)
        sys.exit(2)

    exact, ci = {}, {}
    for k, v in raw.items():
        if k is None or v is None:
            continue
        ks, vs = str(k).strip(), str(v).strip()
        if not ks or not vs:
            continue
        exact[ks] = vs
        ci[ks.lower()] = vs
    return exact, ci

# --- Domain row models ---------------------------------------------------------
@dataclass(frozen=True)
class ShinyAppRow:
    id: str
    product_name: str
    set_name: str
    brand_name: str
    discriminator: str
    rarity: str
    quantity: str
    value_total: str
    value_per_unit: str
    value_currency: str
    paid_total: str
    paid_per_unit: str
    paid_currency: str
    grade_type: str
    grade_subtype: str
    group_name: str
    group_wishlist: str
    tcg_player_id: str
    price_charting_id: str
    card_market_id: str
    date_added: str
    tag: str

    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> "ShinyAppRow":
        g = lambda k: "" if row.get(k) is None else str(row.get(k))
        return cls(
            id=g("id"),
            product_name=g("product_name"),
            set_name=g("set_name"),
            brand_name=g("brand_name"),
            discriminator=g("discriminator"),
            rarity=g("rarity"),
            quantity=g("quantity"),
            value_total=g("value_total"),
            value_per_unit=g("value_per_unit"),
            value_currency=g("value_currency"),
            paid_total=g("paid_total"),
            paid_per_unit=g("paid_per_unit"),
            paid_currency=g("paid_currency"),
            grade_type=g("grade_type"),
            grade_subtype=g("grade_subtype"),
            group_name=g("group_name"),
            group_wishlist=g("group_wishlist"),
            tcg_player_id=g("tcg_player_id"),
            price_charting_id=g("price_charting_id"),
            card_market_id=g("card_market_id"),
            date_added=g("date_added"),
            tag=g("tag"),
        )

@dataclass(frozen=True)
class MoxfieldAppRow:
    count: str
    tradelist_count: str
    name: str
    edition: str
    condition: str
    language: str
    foil: str
    tags: str
    last_modified: str
    collector_number: str
    alter: str
    proxy: str
    purchase_price: str

    group_name: str

    @classmethod
    def from_shiny(cls, shiny: ShinyAppRow, exact_map: Dict[str, str], ci_map: Dict[str, str]) -> "MoxfieldAppRow":
        is_foil = ""
        if "foil" in shiny.rarity.lower():
            is_foil = "foil"
        return cls(
            count=shiny.quantity,
            tradelist_count=shiny.quantity,
            name=clean_name(shiny.product_name),
            edition=_edition_code(shiny.set_name, exact_map, ci_map).lower(), # always use lowercase edition names for Moxfield
            condition=shiny.grade_subtype,
            language="English",
            foil=is_foil,
            tags="",
            last_modified=_format_last_modified(shiny.date_added),
            collector_number=_collector_number(shiny.discriminator),
            alter="False",
            proxy="False",
            purchase_price="",
            group_name = shiny.group_name
        )

    def to_csv_dict(self) -> Dict[str, str]:
        return {
            "Count": self.count,
            "Tradelist Count": self.tradelist_count,
            "Name": self.name,
            "Edition": self.edition,
            "Condition": self.condition,
            "Language": self.language,
            "Foil": self.foil,
            "Tags": self.tags,
            "Last Modified": self.last_modified,
            "Collector Number": self.collector_number,
            "Alter": self.alter,
            "Proxy": self.proxy,
            "Purchase Price": self.purchase_price,
        }

    def to_deck_txt(self) -> str:
        parts = [
            self.count,
            self.name,
            "(" + self.edition.upper()  + ")",
            self.collector_number
        ]
        if self.foil != "":
            parts.append("*F*")
        return " ".join(parts)

    def make_deck_filename(self) -> str:
        filename = "deck_" + self.group_name + ".txt"
        filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
        return filename

# --- Core processing -----------------------------------------------------------
def process(reader: csv.DictReader, writer: csv.DictWriter, exact_map: Dict[str, str], ci_map: Dict[str, str]) -> None:
    decks_created = set()
    writer.writeheader()
    for row in reader:
        shiny = ShinyAppRow.from_csv_row(row)
        mox = MoxfieldAppRow.from_shiny(shiny, exact_map, ci_map)
        deck_filename = mox.make_deck_filename()
        # clear the file contents for writing
        if deck_filename not in decks_created:
            with open(deck_filename, "w") as _:
                pass
            decks_created.add(deck_filename)
        append_line_to_file(mox.make_deck_filename(), mox.to_deck_txt())
        writer.writerow(mox.to_csv_dict())

def clean_name(name: str) -> str:
    # remove trailing parenthesis;
    # "Thornbite Staff (White Border)"
    new_name = re.sub('\(.*\)', '', name)
    # remove trailing descriptors
    # "Mountain - Full Art"
    new_name = re.sub(' - Full Art$', '', new_name)
    new_name = re.sub(' - JP Full Art$', '', new_name)
    # catch some special cards with alternate names embedded
    # Anguirus, Armored Killer - Gemrazer
    new_name = re.sub('^.* - ', '', new_name)
    return new_name.strip()

def append_line_to_file(filename: str, line: str):
    with open(filename, 'a') as fout:
        fout.write(line + '\n')

# --- CLI -----------------------------------------------------------------------
def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert ShinyApp CSV rows to Moxfield CSV format.")
    p.add_argument("input", help="Path to input CSV file (use '-' for stdin)")
    p.add_argument("--sets", default=default_sets_json, help="Path to JSON file with { 'Set Name': 'setcode', ... }")
    return p.parse_args(argv)

def main() -> int:
    args = parse_args(sys.argv[1:])
    exact_map, ci_map = load_set_mapping(args.sets)

    # writer = csv.DictWriter(sys.stdout, fieldnames=MOXFIELD_FIELDS, quoting=csv.QUOTE_ALL)
    output_filename = default_output_filename
    fout = open(output_filename, "w")
    writer = csv.DictWriter(fout, fieldnames=MOXFIELD_FIELDS, quoting=csv.QUOTE_ALL)

    if args.input == "-":
        reader = csv.DictReader(sys.stdin)
        process(reader, writer, exact_map, ci_map)
    else:
        with open(args.input, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            process(reader, writer, exact_map, ci_map)

    return 0

if __name__ == "__main__":
    sys.exit(main())
