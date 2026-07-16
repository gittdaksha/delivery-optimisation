import pandas as pd                              # table/dataframe library
import sqlite3                                   # built-in Python SQLite driver
import os                                        # interact with file system

DB_PATH = 'data/delivery_db.sqlite'             # path to the database file
CSV_PATH = 'data/raw/deliveries.csv'            # path to the source CSV

def load_to_db():
    print(f"Loading {CSV_PATH} into SQLite database...")

    # STEP 1 — EXTRACT: read the raw file into memory
    # SQL cannot open files — Python must read it first
    df = pd.read_csv(CSV_PATH)                   # read CSV into a DataFrame (table in memory)

    # STEP 2 — open (or create) the SQLite database file on disk
    # if the file doesn't exist, sqlite3 creates it automatically
    conn = sqlite3.connect(DB_PATH)

    # STEP 3 — LOAD raw data into database
    # if_exists='replace' = drop and recreate table if it already exists (safe re-run)
    # index=False = don't write pandas row numbers as a column in the database
    df.to_sql('deliveries', conn, if_exists='replace', index=False)
    print(f"  Loaded {len(df):,} rows into 'deliveries' table")

    # STEP 4 — TRANSFORM: pre-compute FADR summary table
    # WHY: querying 50,000 rows every time the dashboard loads is slow
    # pre-calculating and storing the summary = dashboard stays fast
    # e.g. Mumbai + Apartment → 1200 attempts, 800 successes → FADR = 0.667
    #
    # COLUMNS USED FROM df:
    # 'city'          → comes from generate_data.py → random.choice(CITIES)
    # 'address_type'  → comes from generate_data.py → random.choice(ADDRESS_TYPES)
    # 'is_successful' → comes from generate_data.py → int(is_successful) → 0 or 1
    #                   used TWICE: once for count (total attempts), once for sum (successes)
    fadr = (
        df.groupby(['city', 'address_type'])     # group rows by city + address type
        .agg(
            total_attempts=('is_successful', 'count'),  # count total rows per group
            successful=('is_successful', 'sum')         # sum of 1s = count of successes
            # e.g. [1,0,1,1,0] → count=5, sum=3
        )
        .reset_index()                           # turn group keys back into regular columns
    )
    # FADR = successes / total attempts
    # uses 'successful' and 'total_attempts' columns created by .agg() above
    # e.g. 800 / 1200 = 0.667 = 66.7% first attempt delivery rate
    fadr['fadr'] = fadr['successful'] / fadr['total_attempts']

    # STEP 5 — LOAD summary table into database (second table alongside raw data)
    fadr.to_sql('fadr_by_segment', conn, if_exists='replace', index=False)
    print(f"  Computed FADR for {len(fadr)} city/address-type segments")

    conn.close()                                 # always close the connection when done
    print(f"\nDatabase saved to {DB_PATH}")

if __name__ == '__main__':                       # only runs when called directly
    load_to_db()