#!/usr/bin/env python3
import sys
import csv
import argparse
import re
import os
from typing import List #Dict, Any, , Tuple

# USAGE:
# copy / paste the table from the page here https://store.tcgplayer.com/collection into a .csv file
# then run this script against it
# then import the output to https://moxfield.com/collection

# example TCGPlayer collection table format;

# Have,Want,Trade,Name,Set,Low,Mid,High
# 1,0,0, Youthful Valkyrie (Borderless) - [Foil],Foundations,$0.44,$0.79,$9.64
# 1,0,0," Ruby, Daring Tracker",Foundations,$0.03,$0.20,"$1,000.12"
# 1,0,0," Giada, Font of Hope",Foundations,$0.50,$1.26,$7.61
# 4,0,0, Plains (0282) - [Foil],Foundations,$0.19,$0.68,$99.97
# 10,0,0, Plains (0283) - [Foil],Foundations,$0.15,$0.42,$8.69
# 1,0,0, Angel of Finality,Foundations,$0.01,$0.20,$20.00
# 1,0,0, Forest (0291) - [Foil],Foundations,$0.13,$0.55,$99.90
# 5,0,0, Forest (0290) - [Foil],Foundations,$0.05,$0.38,$8.69
# 10,0,0, Mountain (0289) - [Foil],Foundations,$0.08,$0.31,$99.81

this_file_path = os.path.realpath(__file__)
this_dir_path = os.path.dirname(this_file_path)
set_codes_file = os.path.join(this_dir_path, "moxfield_set_codes.csv" )# https://moxfield.com/sets
default_output_filename = "tcgplayer-converted-collection.csv"

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
    "Playtest Card",
    "Purchase Price",
]

def clean_name(name: str) -> str:
    # remove trailing parenthesis;
    # "Thornbite Staff (White Border)"
    new_name = re.sub('\(.*\)', '', name)
    # remove trailing descriptors
    # "Mountain - Full Art"
    # new_name = re.sub(' - Full Art$', '', new_name)
    # new_name = re.sub(' - JP Full Art$', '', new_name)
    # catch some special cards with alternate names embedded
    # Anguirus, Armored Killer - Gemrazer
    # Godzilla, Doom Inevitable - Yidaro, Wandering Monster
    # Godzilla, King of the Monsters - Zilortha, Strength Incarnate
    # Godzilla, Primeval Champion - Titanoth Rex
    new_name = re.sub(' - .*$', '', new_name)
    return new_name.strip()


def process(reader: csv.DictReader, writer: csv.DictWriter) -> None:
    # load the Set Codes from file
    set_codes = {}
    with open(set_codes_file) as fin:
        codesReader = csv.DictReader(fin)
        for row in codesReader:
            set_codes[row["Set Name"]] = row["SetCode"]

    # start writing output
    writer.writeheader()
    for row in reader:
        is_foil = ""
        if "[foil]" in row["Name"].lower():
            is_foil = "TRUE"
        output_row = {
            "Count": row["Have"],
            "Name": clean_name(row["Name"]),
            "Edition": "",
            "Foil": is_foil
        }
        if row["Set"] in set_codes.keys():
            output_row["Edition"] = set_codes[row["Set"]]
        writer.writerow(output_row)


# --- CLI -----------------------------------------------------------------------
def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert TCGPlayer Collection CSV rows to Moxfield CSV format.")
    p.add_argument("input", help="Path to input CSV file (use '-' for stdin)")
    return p.parse_args(argv)

def main() -> int:
    args = parse_args(sys.argv[1:])

    output_filename = default_output_filename
    fout = open(output_filename, "w")
    writer = csv.DictWriter(fout, fieldnames=MOXFIELD_FIELDS, quoting=csv.QUOTE_ALL)

    if args.input == "-":
        reader = csv.DictReader(sys.stdin)
        process(reader, writer)
    else:
        with open(args.input, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            process(reader, writer)

    return 0

if __name__ == "__main__":
    sys.exit(main())
