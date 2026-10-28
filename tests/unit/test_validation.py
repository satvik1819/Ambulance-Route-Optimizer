from src.utils.validation import validate_dataset
def test_dataset():
 r=validate_dataset("data/raw");assert r["valid"],r["errors"];assert r["counts"]["nodes.csv"]==2000 and r["counts"]["roads.csv"]==6000
