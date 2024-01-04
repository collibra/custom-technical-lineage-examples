import unittest

from src.helper import get_asset_types_name_from_lineage_json_file


class HelperTest(unittest.TestCase):
    def test_get_asset_types_name_from_lineage_json_file(self):
        result = get_asset_types_name_from_lineage_json_file("test_data/conversion/lineage_v3.json")
        assert result == {"System", "Schema", "Database", "Table", "Column"}
