#!/usr/bin/env python3
import csv
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

"""
Convert the Shiny app Export .csv into a format that can be imported by Moxfield (https://moxfield.com/collection)

USAGE:

./shiny-to-moxfield.py ../ShinyExport-fedfe0e51d11449ab31763ff769b09b1.csv > ../moxfield_tmp.csv
"""

set_name_to_code = {
    'Limited Edition Alpha': 'LEA',
    'Limited Edition Beta': 'LEB',
    'Unlimited Edition': '2ED',
    'Revised Edition': '3ED',
    'Fourth Edition': '4ED',
    'Fifth Edition': '5ED',
    'Classic Sixth Edition': '6ED',
    'Seventh Edition': '7ED',
    'Eighth Edition': '8ED',
    'Ninth Edition': '9ED',
    'Tenth Edition': '10E',
    'Magic 2010': 'M10',
    'Magic 2011': 'M11',
    'Magic 2012': 'M12',
    'Magic 2013': 'M13',
    'Magic 2014': 'M14',
    'Magic 2015': 'M15',
    'Magic Origins': 'ORI',
    'Core Set 2019': 'M19',
    'Core Set 2020': 'M20',
    'Core Set 2021': 'M21',
    'Magic: The Gathering Foundations': 'FDN',
    'Arabian Nights': 'ARN',
    'Antiquities': 'ATQ',
    'Legends': 'LEG',
    'The Dark': 'DRK',
    'Fallen Empires': 'FEM',
    'Ice Age': 'ICE',
    'Homelands': 'HML',
    'Alliances': 'ALL',
    'Mirage': 'MIR',
    'Visions': 'VIS',
    'Weatherlight': 'WTH',
    'Tempest': 'TMP',
    'Stronghold': 'STH',
    'Exodus': 'EXO',
    "Urza's Saga": 'USG',
    "Urza's Legacy": 'ULG',
    "Urza's Destiny": 'UDS',
    'Mercadian Masques': 'MMQ',
    'Nemesis': 'NEM',
    'Prophecy': 'PCY',
    'Invasion': 'INV',
    'Planeshift': 'PLS',
    'Apocalypse': 'APC',
    'Odyssey': 'ODY',
    'Torment': 'TOR',
    'Judgment': 'JUD',
    'Onslaught': 'ONS',
    'Legions': 'LGN',
    'Scourge': 'SCG',
    'Mirrodin': 'MRD',
    'Darksteel': 'DST',
    'Fifth Dawn': '5DN',
    'Champions of Kamigawa': 'CHK',
    'Betrayers of Kamigawa': 'BOK',
    'Saviors of Kamigawa': 'SOK',
    'Ravnica: City of Guilds': 'RAV',
    'Guildpact': 'GPT',
    'Dissension': 'DIS',
    'Coldsnap': 'CSP',
    'Planar Chaos': 'PLC',
    'Future Sight': 'FUT',
    'Lorwyn': 'LRW',
    'Morningtide': 'MOR',
    'Shadowmoor': 'SHM',
    'Eventide': 'EVE',
    'Shards of Alara': 'ALA',
    'Conflux': 'CON',
    'Alara Reborn': 'ARB',
    'Zendikar': 'ZEN',
    'Worldwake': 'WWK',
    'Rise of the Eldrazi': 'ROE',
    'Scars of Mirrodin': 'SOM',
    'Mirrodin Besieged': 'MBS',
    'New Phyrexia': 'NPH',
    'Innistrad': 'ISD',
    'Dark Ascension': 'DKA',
    'Avacyn Restored': 'AVR',
    'Return to Ravnica': 'RTR',
    'Gatecrash': 'GTC',
    "Dragon's Maze": 'DGM',
    'Theros': 'THS',
    'Born of the Gods': 'BNG',
    'Journey into Nyx': 'JOU',
    'Khans of Tarkir': 'KTK',
    'Fate Reforged': 'FRF',
    'Dragons of Tarkir': 'DTK',
    'Battle for Zendikar': 'BFZ',
    'Oath of the Gatewatch': 'OGW',
    'Shadows over Innistrad': 'SOI',
    'Eldritch Moon': 'EMN',
    'Kaladesh': 'KLD',
    'Aether Revolt': 'AER',
    'Amonkhet': 'AKH',
    'Hour of Devastation': 'HOU',
    'Ixalan': 'XLN',
    'Rivals of Ixalan': 'RIX',
    'Dominaria': 'DOM',
    'Guilds of Ravnica': 'GRN',
    'Ravnica Allegiance': 'RNA',
    'War of the Spark': 'WAR',
    'Throne of Eldraine': 'ELD',
    'Theros Beyond Death': 'THB',
    'Ikoria: Lair of Behemoths': 'IKO',
    'Zendikar Rising': 'ZNR',
    'Kaldheim': 'KHM',
    'Strixhaven: School of Mages': 'STX',
    'Dungeons & Dragons: Adventures in the Forgotten Realms': 'AFR',
    'Innistrad: Midnight Hunt': 'MID',
    'Innistrad: Crimson Vow': 'VOW',
    'Kamigawa: Neon Dynasty': 'NEO',
    'Streets of New Capenna': 'SNC',
    'Dominaria United': 'DMU',
    "The Brothers' War": 'BRO',
    'Phyrexia: All Will Be One': 'ONE',
    'March of the Machine': 'MOM',
    'March of the Machine: The Aftermath': 'MAT',
    'Wilds of Eldraine': 'WOE',
    'The Lost Caverns of Ixalan': 'LCI',
    'Murders at Karlov Manor': 'MKM',
    'Outlaws of Thunder Junction': 'OTJ',
    'Bloomburrow': 'BLB',
    'Duskmourn: House of Horror': 'DSK',
    'Aetherdrift': 'DFT',
    'Tarkir: Dragonstorm': 'TDM',
    'Final Fantasy': 'FIN',
    'Edge of Eternities': 'EOE',
    "Marvel's Spider-Man": 'SPM',
    'Avatar: The Last Airbender': 'TLA',
    'Lorwyn Eclipsed': 'TBA',
    'Secrets of Strixhaven': 'TBA',
    'Event set': 'TBA',
    'TBA': 'TBA',
    'Modern Horizons': 'MH1',
    'Modern Horizons 2': 'MH2',
    'The Lord of the Rings: Tales of Middle-earth': 'LTR',
    'Modern Horizons 3': 'MH3',
    'Portal': 'POR',
    'Portal Second Age': 'P02',
    'Portal Three Kingdoms': 'PTK',
    'Starter 1999': 'S99',
    'Starter 2000': 'S00',
    'Global Series: Jiang Yanggu & Mu Yanling': 'GS1',
    'Chronicles': 'CHR',
    'Anthologies': 'ATH',
    'Battle Royale Box Set': 'BRB',
    'Beatdown Box Set': 'BTD',
    'Deckmasters: Garfield vs. Finkel': 'DKM',
    'Duels of the Planeswalkers (decks)': 'DPA',
    'Modern Event Deck': 'MD1',
    'Mystery Booster': 'MB1',
    'Time Spiral Remastered': 'TSR',
    'Dominaria Remastered': 'DMR',
    'Ravnica Remastered': 'RVR',
    'Innistrad Remastered': 'INR',
    'Mystery Booster 2': 'MB2',
    'Duel Decks: Elves vs. Goblins': 'EVG',
    'Duel Decks: Jace vs. Chandra': 'DD2',
    'Duel Decks: Divine vs. Demonic': 'DDC',
    'Duel Decks: Garruk vs. Liliana': 'DDD',
    'Duel Decks: Phyrexia vs. the Coalition': 'DDE',
    'Duel Decks: Elspeth vs. Tezzeret': 'DDF',
    'Duel Decks: Knights vs. Dragons': 'DDG',
    'Duel Decks: Ajani vs. Nicol Bolas': 'DDH',
    'Duel Decks: Venser vs. Koth': 'DDI',
    'Duel Decks: Izzet vs. Golgari': 'DDJ',
    'Duel Decks: Sorin vs. Tibalt': 'DDK',
    'Duel Decks: Heroes vs. Monsters': 'DDL',
    'Duel Decks: Jace vs. Vraska': 'DDM',
    'Duel Decks: Speed vs. Cunning': 'DDN',
    'Duel Decks Anthology': 'DD3',
    'Duel Decks: Elspeth vs. Kiora': 'DDO',
    'Duel Decks: Zendikar vs. Eldrazi': 'DDP',
    'Duel Decks: Blessed vs. Cursed': 'DDQ',
    'Duel Decks: Nissa vs. Ob Nixilis': 'DDR',
    'Duel Decks: Mind vs. Might': 'DDS',
    'Duel Decks: Merfolk vs. Goblins': 'DDT',
    'Duel Decks: Elves vs. Inventors': 'DDU',
    'From the Vault: Dragons': 'DRB',
    'From the Vault: Exiled': 'V09',
    'From the Vault: Relics': 'V10',
    'From the Vault: Legends': 'V11',
    'From the Vault: Realms': 'V12',
    'From the Vault: Twenty': 'V13',
    'From the Vault: Annihilation': 'V14',
    'From the Vault: Angels': 'V15',
    'From the Vault: Lore': 'V16',
    'From the Vault: Transform': 'V17',
    'Signature Spellbook: Jace': 'SS1',
    'Signature Spellbook: Gideon': 'SS2',
    'Signature Spellbook: Chandra': 'SS3',
    'Premium Deck Series: Slivers': 'H09',
    'Premium Deck Series: Fire and Lightning': 'PD2',
    'Premium Deck Series: Graveborn': 'PD3',
    'Modern Masters': 'MMA',
    'Modern Masters 2015 Edition': 'MM2',
    'Eternal Masters': 'EMA',
    'Modern Masters 2017 Edition': 'MM3',
    'Iconic Masters': 'IMA',
    'Masters 25': 'A25',
    'Ultimate Masters': 'UMA',
    'Double Masters': '2XM',
    'Double Masters 2022 Edition': '2X2',
    'Commander Masters': 'CMM',
    "Deck Builder's Toolkit": 'w10',
    "Deck Builder's Toolkit (Refreshed Version)": 'w11',
    "Deck Builder's Toolkit (2012 Edition)": 'w12',
    "Deck Builder's Toolkit (2014 Core Set Edition)": 'w14',
    "Deck Builder's Toolkit (2015 Core Set Edition)": 'w15',
    "Deck Builder's Toolkit (Magic Origins Edition)": 'ORI',
    "Deck Builder's Toolkit (Shadows over Innistrad Edition)": 'w16',
    "Deck Builder's Toolkit (Amonkhet Edition)": 'w17',
    "Deck Builder's Toolkit (Ixalan Edition)": 'w17',
    'Zendikar Expeditions': 'EXP',
    'Kaladesh Inventions': 'MPS',
    'Amonkhet Invocations': 'MP2',
    'Guilds of Ravnica Mythic Edition': 'MED',
    'Ravnica Allegiance Mythic Edition': 'MED',
    'War of the Spark Mythic Edition': 'MED',
    'Strixhaven Mystical Archive': 'STA',
    "The Brothers' War Retro Artifacts": 'BRR',
    'Multiverse Legends': 'MUL',
    'Enchanting Tales': 'WOT',
    'Breaking News': 'OTP',
    'Jumpstart': 'JMP',
    'Jumpstart 2022': 'J22',
    'Foundations Jumpstart': 'J25',
    'Secret Lair Drop': 'SLD',
    '"Universes Within"': 'SLX',
    'Transformers': 'BOT',
    'Doctor Who': 'WHO',
    'Jurassic World': 'REX',
    'Fallout': 'PIP',
    'Assassin’s Creed': 'ACR',
    'Planechase': 'HOP',
    'Planechase 2012 Edition': 'PC2',
    'Planechase Anthology': 'PCA',
    'Archenemy': 'ARC',
    'Archenemy: Nicol Bolas': 'E01',
    'Commander 2011': 'CMD',
    "Commander's Arsenal": 'CM1',
    'Commander 2013 Edition': 'C13',
    'Commander 2014': 'C14',
    'Commander 2015': 'C15',
    'Commander 2016': 'C16',
    'Commander Anthology': 'CMA',
    'Commander 2017': 'C17',
    'Commander Anthology Volume II': 'CM2',
    'Commander 2018': 'C18',
    'Commander 2019': 'C19',
    'Commander 2020 / Ikoria Commander': 'C20',
    'Zendikar Rising Commander': 'ZNC',
    'Commander Legends': 'CMR',
    'Kaldheim Commander': 'KHC',
    'Commander 2021 / Strixhaven Commander': 'C21',
    'Forgotten Realms Commander': 'AFC',
    'Midnight Hunt Commander': 'MIC',
    'Crimson Vow Commander': 'VOC',
    'Neon Dynasty Commander': 'NEC',
    'New Capenna Commander': 'NCC',
    "Battle for Baldur's Gate / Commander Legends 2": 'CLB',
    'Warhammer 40,000 Commander': '40K',
    "The Brothers' War Commander": 'BRC',
    'Wilds of Eldraine Commander': 'WOC',
    'Conspiracy': 'CNS',
    'Conspiracy: Take the Crown': 'CN2',
    'Explorers of Ixalan': 'E02',
    'Battlebond': 'BBD',
    "Collector's Edition": 'CED',
    "International Collector's Edition": 'CEI',
    'Unglued': 'UGL',
    'Unhinged': 'UNH',
    'Unstable': 'UST',
    'Unsanctioned': 'UND',
    'Unfinity': 'UNF',
    'Masters Edition': 'MED',
    'Masters Edition II': 'ME2',
    'Masters Edition III': 'ME3',
    'Masters Edition IV': 'ME4',
    'Vintage Masters': 'VMA',
    'Tempest Remastered': 'TPR'}


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
    """
    Convert input ISO-like strings to 'YYYY-MM-DD HH:MM:SS.ssssss'.
    Falls back to the original string on parse failure.
    Accepts 'Z' (UTC) suffix and timezone offsets.
    """
    if not date_str:
        return ""

    s = date_str.strip()
    try:
        # Allow trailing Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        # Normalize to naive (no tz) but preserve wall-clock value
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        # Best effort: pass through
        return date_str


def _collector_number(discriminator: str) -> str:
    return (discriminator or "").lstrip("#").strip()


def _edition_code(set_name: str, mapping: Dict[str, str]) -> str:
    name = (set_name or "").strip()
    return mapping.get(name, name)  # fallback to original name if unknown


# --- Domain row models ---------------------------------------------------------
@dataclass(frozen=True)
class ShinyAppRow:
    """
    Represents one input row from the 'Shiny App' CSV.
    Construct directly from the csv.DictReader row.
    """
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
        # Use .get for resilience; coerce to str or "" to avoid KeyErrors
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
    """
    Represents one output row for the Moxfield CSV format.
    Build from a ShinyAppRow plus any mapping/config you need.
    """
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

    @classmethod
    def from_shiny(cls, shiny: ShinyAppRow, mapping: Dict[str, str]) -> "MoxfieldAppRow":
        return cls(
            count=shiny.quantity,
            tradelist_count=shiny.quantity,
            name=shiny.product_name,
            edition=_edition_code(shiny.set_name, mapping),
            condition=shiny.grade_subtype,  # e.g. Near Mint
            language="English",
            foil="",               # adjust if you derive foil from tags/names
            tags="",               # populate if you want to carry tags/group
            last_modified=_format_last_modified(shiny.date_added),
            collector_number=_collector_number(shiny.discriminator),
            alter="False",
            proxy="False",
            purchase_price="",     # or shiny.paid_per_unit if you prefer
        )

    def to_csv_dict(self) -> Dict[str, str]:
        """
        Return a dict ready for csv.DictWriter with the expected field names.
        """
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

def main(fin, stdout) -> int:
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(stdout, fieldnames=MOXFIELD_FIELDS, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for row in reader:
        shiny = ShinyAppRow.from_csv_row(row)
        mox = MoxfieldAppRow.from_shiny(shiny, set_name_to_code)
        writer.writerow(mox.to_csv_dict())

    return 0

if __name__ == "__main__":
    input_file = sys.argv[1]
    fin = open(input_file)
    sys.exit(main(fin, sys.stdout))