import pandas as pd                              # pd = table/dataframe library
import numpy as np                               # np = math and array library
from faker import Faker                          # generates realistic fake data
import random                                    # built-in random number tools
from datetime import datetime, timedelta         # datetime = dates, timedelta = date math
import os                                        # interact with file system

fake = Faker('en_IN')  # Indian locale for realistic addresses
np.random.seed(42)                               # seed = same data every run
random.seed(42)                                  # 42 is arbitrary; any int works

ADDRESS_TYPES = ['Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community']  # possible address categories
DELIVERY_WINDOWS = ['Morning (9-12)', 'Afternoon (12-15)', 'Evening (15-19)', 'Night (19-22)']  # time slots
FAILURE_REASONS = ['Customer Unavailable', 'Wrong Address', 'Refused Delivery', 'Building Access Denied', None]  # why fail
CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Pune', 'Chennai']  # cities in dataset

def generate_delivery_data(n_records=50000):     # default = 50000 rows
    records = []                                 # empty list, filled row by row

    for _ in range(n_records):                   # _ = loop counter we don't need
        city = random.choice(CITIES)             # pick one city at random
        address_type = random.choice(ADDRESS_TYPES)  # pick one address type
        window = random.choice(DELIVERY_WINDOWS)     # pick one time window
        # random.uniform(150, 8000) → random float between 150 and 8000, e.g. 3452.7891
        # round(..., 2)              → round to 2 decimal places → 3452.79
        order_value = round(random.uniform(150, 8000), 2)  # random Rs 150-8000

        # Business rules that affect delivery success (mirroring real-world patterns)
        success_prob = 0.78  # baseline FADR (First Attempt Delivery Rate)

        if address_type in ['Apartment', 'PG/Hostel']:
            success_prob -= 0.12  # harder to access
        if address_type == 'Office':
            success_prob += 0.10  # usually someone available
        if window == 'Morning (9-12)':
            success_prob -= 0.15  # most people at work
        if window == 'Evening (15-19)':
            success_prob += 0.08  # people returning home
        if window == 'Night (19-22)':
            success_prob += 0.12  # people at home
        if order_value > 5000:
            success_prob -= 0.05  # high value = hand-over only, stricter

        # max(0.10, min(0.97, success_prob)) is a "clamp" pattern:
        #   min(0.97, success_prob) → cap at 0.97 (never exceed 97%)
        #   max(0.10, ...)          → floor at 0.10 (never drop below 10%)
        # e.g. if success_prob computed to 1.05 → min gives 0.97 → max gives 0.97
        # e.g. if success_prob computed to 0.03 → min gives 0.03 → max gives 0.10
        success_prob = max(0.10, min(0.97, success_prob))  # clamp: keep between 10%-97%
        is_successful = random.random() < success_prob     # True if random < threshold

        failure_reason = None                    # assume success; overwrite if failed
        if not is_successful:
            failure_reason = random.choice(FAILURE_REASONS[:-1])  # exclude None

        attempt_date = datetime.now() - timedelta(days=random.randint(1, 365))  # random past date

        records.append({
            'delivery_id': fake.uuid4(),         # unique delivery ID (UUID)
            'customer_id': fake.uuid4()[:8],     # short 8-char customer ID
            'city': city,                        # which city
            'address_type': address_type,        # apartment / office / etc
            'delivery_window': window,           # time slot chosen
            'order_value': order_value,          # Rs value of the order
            'is_successful': int(is_successful), # 1 = delivered, 0 = failed
            'failure_reason': failure_reason,    # None if delivery succeeded
            'attempt_number': random.choices([1, 2, 3], weights=[70, 22, 8])[0],  # 70% first-attempt
            'attempt_date': attempt_date.strftime('%Y-%m-%d'),  # format: YYYY-MM-DD string
            'attempt_hour': int(window.split('(')[1].split('-')[0]),  # extract start hour from window
            'has_delivery_preference': random.choices([0, 1], weights=[60, 40])[0],  # 40% set preference
            'proximity_alert_sent': random.choices([0, 1], weights=[55, 45])[0],    # 45% got alert
        })

    return pd.DataFrame(records)                 # convert list of dicts to a table


if __name__ == '__main__':                       # only runs when called directly
    print("Generating 50,000 delivery records...")
    df = generate_delivery_data(50000)           # call the function above

    os.makedirs('data/raw', exist_ok=True)       # create folder; ok if already exists
    output_path = 'data/raw/deliveries.csv'      # where to save the file
    df.to_csv(output_path, index=False)          # index=False = don't save row numbers

    print(f"Saved to {output_path}")
    print(f"Shape: {df.shape}")                  # shape = (rows, columns) e.g. (50000, 13)
    print(f"\nOverall FADR: {df['is_successful'].mean():.2%}")  # .mean() on 0/1 column = rate
    print(f"\nFADR by address type:")
    print(df.groupby('address_type')['is_successful'].mean().sort_values())  # group → avg → sort
    print(f"\nFADR by delivery window:")
    print(df.groupby('delivery_window')['is_successful'].mean().sort_values())  # lowest FADR first