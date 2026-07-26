import pandas as pd  # needed to work with DataFrames in tests
import sys  # used to modify the Python import path
import os  # used to build the path to the src folder

# sys.path = the list of folders Python searches when you write "import something"
# sys.path.insert(0, ...) = add a new folder at position 0 (first in the search list)
# this is needed because test files live in tests/ but the code lives in src/
# without this, "from generate_data import ..." would fail with ModuleNotFoundError
#
# os.path.dirname(__file__) = the absolute path of the current test file's folder
#   e.g. "C:/Users/Daksha/project/tests"
# os.path.join(..., '..', 'src') = go up one level (..) then into src/
#   e.g. "C:/Users/Daksha/project/tests/../src" which resolves to "C:/Users/Daksha/project/src"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate_data import generate_delivery_data  # import the function to test


def test_generated_data_shape():  # test: function creates correct number of rows/cols
    df = generate_delivery_data(n_records=100)
    # assert <condition>, "message" = if condition is False, the test FAILS with that message
    # assert True → test passes silently
    # assert False → test fails and pytest prints "Should generate exactly 100 records"
    # df.shape returns (rows, columns) as a tuple; [0] = rows, [1] = columns
    assert df.shape[0] == 100, "Should generate exactly 100 records"  # check row count
    assert df.shape[1] == 13,  "Should have 13 columns"  # check column count


def test_no_null_delivery_ids():  # test: every row has a delivery_id
    df = generate_delivery_data(n_records=100)
    assert df['delivery_id'].isnull().sum() == 0, "delivery_id must never be null"  # 0 nulls expected


def test_is_successful_is_binary():  # test: column must only contain 0 or 1
    df = generate_delivery_data(n_records=500)
    # .unique() = returns array of distinct values found in the column, e.g. [0, 1]
    # set(...) = convert to a Python set so we can use .issubset()
    values = set(df['is_successful'].unique())  # get all unique values in the column
    # .issubset({0, 1}) = True if 'values' contains only elements from {0, 1}
    # if values = {0, 1, 2} then issubset returns False → test fails
    assert values.issubset({0, 1}), f"is_successful must be 0 or 1, got: {values}"


def test_fadr_is_reasonable():  # test: overall success rate is in expected range
    df = generate_delivery_data(n_records=5000)
    fadr = df['is_successful'].mean()  # average of 0/1 column = success rate
    # 0.5 < fadr < 0.95 = Python chained comparison: fadr must be between 0.5 and 0.95
    # f"{fadr:.2%}" = format as percentage with 2 decimals → e.g. 0.753 → "75.30%"
    assert 0.5 < fadr < 0.95, f"FADR {fadr:.2%} is outside expected range 50-95%"


def test_failure_reason_null_when_successful():  # test: no failure reason on successes
    df = generate_delivery_data(n_records=500)
    # Successful deliveries should not have a failure reason
    # (df['is_successful'] == 1) = True/False column: True where delivery succeeded
    # (df['failure_reason'].notnull()) = True/False column: True where reason is NOT null
    # & = element-wise AND: both conditions must be True in the same row
    # df[...] = keep only rows where both are True (successful BUT has a failure reason = bug)
    bad_rows = df[(df['is_successful'] == 1) & (df['failure_reason'].notnull())]  # filter bad rows
    assert len(bad_rows) == 0, "Successful deliveries must not have a failure_reason"


def test_address_types_are_valid():  # test: no unexpected address categories
    df = generate_delivery_data(n_records=500)
    valid = {'Apartment', 'PG/Hostel', 'House', 'Office', 'Gated Community'}  # allowed values
    actual = set(df['address_type'].unique())  # values actually in the data
    # actual - valid = set difference: elements in 'actual' that are NOT in 'valid'
    # e.g. if actual = {'Apartment', 'Villa'}, then actual - valid = {'Villa'}
    # this tells you exactly which unexpected values appeared
    assert actual.issubset(valid), f"Unexpected address types: {actual - valid}"  # - = set difference


def test_order_value_positive():  # test: no zero or negative order values
    df = generate_delivery_data(n_records=500)
    # (df['order_value'] > 0) = True/False column: True for each row where value > 0
    # .all() = returns a single True only if every value in the column is True
    # if even one row has order_value <= 0, .all() returns False → test fails
    assert (df['order_value'] > 0).all(), "All order values must be positive"  # .all() = must be true for every row