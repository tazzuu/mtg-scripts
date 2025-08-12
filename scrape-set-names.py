#!/usr/bin/env python3
# ChatGPT 5
import csv
import sys
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.request import urlopen
import json

# get the MTG Set Names and their three-letter codes from Wikipedia
# alternate URL; https://web.archive.org/web/20250812090737/https://en.wikipedia.org/wiki/List_of_Magic:_The_Gathering_sets

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_Magic:_The_Gathering_sets"

# --- tiny HTML -> text helper -------------------------------------------------
def strip_tags(html):
    # remove refs/footnotes like [VI], [ 123 ], etc., and tags
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\[[^\]]*\]", "", text)
    return re.sub(r"\s+", " ", text).strip()

# --- super-lightweight table scraper (stdlib only) ----------------------------
class TableExtractor(HTMLParser):
    """
    Extract all HTML tables as lists of rows (each row = list of cell HTML strings).
    """
    def __init__(self):
        super().__init__()
        self.tables = []
        self._in_table = False
        self._in_tr = False
        self._in_cell = False
        self._cur_table = []
        self._cur_row = []
        self._cur_cell = []
        self._cell_tag = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
            self._cur_table = []
        elif self._in_table and tag == "tr":
            self._in_tr = True
            self._cur_row = []
        elif self._in_tr and tag in ("td", "th"):
            self._in_cell = True
            self._cell_tag = tag
            self._cur_cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            cell_html = "".join(self._cur_cell)
            self._cur_row.append((self._cell_tag, cell_html))
            self._cur_cell = []
            self._cell_tag = None
        elif tag == "tr" and self._in_tr:
            self._in_tr = False
            if self._cur_row:
                self._cur_table.append(self._cur_row)
            self._cur_row = []
        elif tag == "table" and self._in_table:
            self._in_table = False
            if self._cur_table:
                self.tables.append(self._cur_table)
            self._cur_table = []

    def handle_data(self, data):
        if self._in_cell:
            self._cur_cell.append(data)

    def handle_startendtag(self, tag, attrs):
        if self._in_cell:
            # keep self-closing tags minimal (e.g., <br/>)
            if tag == "br":
                self._cur_cell.append(" ")


def fetch_html(url):
    with urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def build_set_mapping():
    """
    Scrape Wikipedia for all tables that contain either:
      - headers: ["Set", "...", "Set code"] OR
      - headers: ["Set", "...", "Expansion code"]
    and return dict: {Set Name -> Set Code}
    """
    html = fetch_html(WIKI_URL)
    parser = TableExtractor()
    parser.feed(html)

    mapping = {}

    for table in parser.tables:
        if not table:
            continue

        # header row = first row where there is at least one <th>
        header_cells = None
        for row in table:
            if any(tag == "th" for tag, _ in row):
                header_cells = [strip_tags(cell_html) for tag, cell_html in row]
                break
        if not header_cells:
            continue

        # normalize header names (case-insensitive)
        norm = [h.lower() for h in header_cells]

        # try to find the relevant columns
        # We need a "Set" column and either "Set code" or "Expansion code"
        set_idx = None
        code_idx = None

        for i, h in enumerate(norm):
            if h == "set":
                set_idx = i
            if "set code" in h or "expansion code" in h or h == "code":
                code_idx = i

        if set_idx is None or code_idx is None:
            continue  # not a table we want

        # iterate data rows (rows after header row)
        started = False
        for row in table:
            # skip until we've passed the header row
            if not started:
                if any(tag == "th" for tag, _ in row):
                    started = True
                continue

            # skip secondary header rows
            if any(tag == "th" for tag, _ in row):
                continue

            cells = [strip_tags(c) for _, c in row]
            if max(set_idx, code_idx) >= len(cells):
                continue

            set_name = cells[set_idx]
            code = cells[code_idx]

            if not set_name or not code:
                continue

            # clean code (avoid "none", punctuation, oddities)
            code_clean = code.strip()
            if code_clean.lower() == "none":
                continue
            code_clean = re.sub(r"[^A-Za-z0-9]", "", code_clean)

            # Wikipedia sometimes lists weird entries; keep plausible 2–5 char codes
            if not (2 <= len(code_clean) <= 5):
                continue

            # Avoid table sections that aren't actual set names (like "Deck Builder's Toolkit")
            # still, user might want those; we keep them if code looks valid.
            mapping[set_name] = code_clean

    return mapping


# --- your CSV → CSV converter using the scraped mapping -----------------------
def main():
    # Build mapping from Wikipedia
    set_name_to_code = build_set_mapping()
    print(json.dumps(set_name_to_code, indent=4))


if __name__ == "__main__":
    main()
