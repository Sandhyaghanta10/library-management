"""Entry point:  python3 -m library [--demo] [--db PATH]"""
import argparse

from .gui import main

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--demo", action="store_true", help="load sample books, members and loans if the library is empty")
parser.add_argument("--db", default="library.db", help="SQLite file to use (default: library.db)")
args = parser.parse_args()
main(args.db, args.demo)
