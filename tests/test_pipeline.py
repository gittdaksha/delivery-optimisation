import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from generate_data import generate_delivery_data

def test_generated_data_shape():
    df = generate_delivery_data(n_records=100)
    assert df.shape[0] == 100
    assert df.shape[1] == 13

def test_no_null_delivery_ids():
    df = generate_delivery_data(n_records=100)
    assert df["delivery_id"].isnull().sum() == 0

def test_is_successful_is_binary():
    df = generate_delivery_data(n_records=500)
    values = set(df["is_successful"].unique())
    assert values.issubset({0, 1})

def test_fadr_is_reasonable():
    df = generate_delivery_data(n_records=5000)
    fadr = df["is_successful"].mean()
    assert 0.5 < fadr < 0.95

def test_failure_reason_null_when_successful():
    df = generate_delivery_data(n_records=500)
    bad_rows = df[(df["is_successful"] == 1) & (df["failure_reason"].notnull())]
    assert len(bad_rows) == 0

def test_address_types_are_valid():
    df = generate_delivery_data(n_records=500)
    valid = {"Apartment", "PG/Hostel", "House", "Office", "Gated Community"}
    actual = set(df["address_type"].unique())
    assert actual.issubset(valid)

def test_order_value_positive():
    df = generate_delivery_data(n_records=500)
    assert (df["order_value"] > 0).all()
