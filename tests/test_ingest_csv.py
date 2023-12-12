import json
import shutil
import unittest
from pathlib import Path

from src.exceptions import InvalidCSVException
from src.models import (
    Asset,
    AssetProperties,
    CustomLineageConfig,
    LeafAsset,
    ParentAsset,
    SourceCode,
    SourceCodeHighLight,
)
from tools.ingest_csv import _create_asset, _create_source_code, _validate_header, ingest_csv_files


class TestIngestCSV(unittest.TestCase):
    def setUp(self):
        self.filename = "./test_data/csv/csv_1.csv"
        self.csv_file_path = Path(self.filename)
        self.custom_lineage_config = CustomLineageConfig(
            application_name="unit tests csv",
            output_directory="./test_data/csv/ingested/",
        )

    def test_validate_header(self):
        invalid_1 = [
            "System",
            "Database",
            "Table",
            "fullname",
            "System",
            "Database",
            "Table",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]
        invalid_2 = [
            "System",
            "Database",
            "Table",
            "fullname",
            "System",
            "fullname",
            "Table",
            "fullname",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]
        invalid_3 = [
            "Database",
            "Table",
            "fullname",
            "System",
            "fullname",
            "Table",
            "fullname",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]
        invalid_4 = [
            "System",
            "Database",
            "Table",
            "fullname",
            "System",
            "fullname",
            "Table",
            "fullname",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]
        invalid_5 = [
            "System",
            "Database",
            "Table",
            "fullname",
            "System",
            "Database",
            "Table",
            "fullname",
            "domain_id",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]

        for invalid_header in [invalid_1, invalid_2, invalid_3, invalid_4, invalid_5]:
            with self.assertRaises(InvalidCSVException):
                _validate_header(headers=invalid_header, csv_file=self.csv_file_path)

        valid_1 = [
            "System",
            "Database",
            "Table",
            "fullname",
            "domain_id",
            "System",
            "Database",
            "Table",
            "fullname",
            "domain_id",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]
        valid_2 = [
            "Database",
            "Table",
            "Column",
            "fullname",
            "domain_id",
            "System",
            "Database",
            "Table",
            "Column",
            "fullname",
            "domain_id",
            "source_code",
            "highlights",
            "transformation_display_name",
        ]

        for valid_header, positions in zip([valid_1, valid_2], [[3, 8], [3, 9]]):
            positions_found = _validate_header(headers=valid_header, csv_file=self.csv_file_path)
            self.assertEqual(positions_found, positions)

    def test_create_source_code(self):
        # empty source_code_text
        self.assertIsNone(
            _create_source_code(
                source_code_text="",
                highlights="",
                transformation_display_name="transformation",
                custom_lineage_config=self.custom_lineage_config,
                line=2,
            )
        )

        # without highlights
        source_code = _create_source_code(
            source_code_text="source code",
            highlights="",
            transformation_display_name="transformation",
            custom_lineage_config=self.custom_lineage_config,
            line=2,
        )
        self.assertIsInstance(source_code, SourceCode)
        self.assertRegex(source_code.path, r"source_codes\/.*\.txt")
        self.assertIsNone(source_code.highlights)
        self.assertEqual(source_code.transformation_display_name, "transformation")

        # with highlights
        source_code = _create_source_code(
            source_code_text="source code",
            highlights="[0:100],[200:300]",
            transformation_display_name="transformation",
            custom_lineage_config=self.custom_lineage_config,
            line=2,
        )
        self.assertIsInstance(source_code, SourceCode)
        self.assertRegex(source_code.path, r"source_codes\/.*\.txt")
        self.assertIsInstance(source_code.highlights[0], SourceCodeHighLight)
        self.assertEqual(source_code.highlights[0], SourceCodeHighLight(start=0, len=100))
        self.assertIsInstance(source_code.highlights[1], SourceCodeHighLight)
        self.assertEqual(source_code.highlights[1], SourceCodeHighLight(start=200, len=300))
        self.assertEqual(source_code.transformation_display_name, "transformation")

        # invalid highlights
        with self.assertRaises(InvalidCSVException):
            source_code = _create_source_code(
                source_code_text="source code",
                highlights="[abc:def]",
                transformation_display_name="transformation",
                custom_lineage_config=self.custom_lineage_config,
                line=2,
            )
        with self.assertRaises(InvalidCSVException):
            source_code = _create_source_code(
                source_code_text="source code",
                highlights="[0-100]",
                transformation_display_name="transformation",
                custom_lineage_config=self.custom_lineage_config,
                line=2,
            )

    def test_create_asset(self):
        dummy_row = ["DB1", "SCH1", "T1", "COL1", "", "", "DB1", "SCH1", "T1", "COL1", "", "", "", "", ""]
        expected_leaf = Asset(name="COL1", type="Column")
        expected_parent = Asset(name="T1", type="Table")
        expected_nodes = [Asset(name="DB1", type="Database"), Asset(name="SCH1", type="Schema")]
        domain_id, fullname = "domain", "fullanme"
        expected_properties = AssetProperties(fullname=fullname, domain_id=domain_id)

        # leaf asset without props
        asset_types = ["Database", "Schema", "Table", "Column"]
        asset_names = ["DB1", "SCH1", "T1", "COL1"]
        created_asset = _create_asset(
            asset_types=asset_types,
            asset_names=asset_names,
            domain_id="",
            fullname="",
            csv_file=self.filename,
            row=dummy_row,
            line=2,
        )
        self.assertIsInstance(created_asset, LeafAsset)
        self.assertIsNone(created_asset.props)
        self.assertEqual(created_asset.leaf, expected_leaf)
        self.assertEqual(created_asset.parent, expected_parent)
        self.assertEqual(created_asset.nodes, expected_nodes)

        # leaf asset with props
        asset_types = ["Database", "Schema", "Table", "Column"]
        asset_names = ["DB1", "SCH1", "T1", "COL1"]
        created_asset = _create_asset(
            asset_types=asset_types,
            asset_names=asset_names,
            domain_id=domain_id,
            fullname=fullname,
            csv_file=self.filename,
            row=dummy_row,
            line=2,
        )
        self.assertIsInstance(created_asset, LeafAsset)
        self.assertIsInstance(created_asset.props, AssetProperties)
        self.assertEqual(created_asset.leaf, expected_leaf)
        self.assertEqual(created_asset.parent, expected_parent)
        self.assertEqual(created_asset.nodes, expected_nodes)
        self.assertEqual(created_asset.props, expected_properties)

        # parent asset without props
        asset_types = ["Database", "Schema", "Table", "Column"]
        asset_names = ["DB1", "SCH1", "T1", ""]
        created_asset = _create_asset(
            asset_types=asset_types,
            asset_names=asset_names,
            domain_id="",
            fullname="",
            csv_file=self.filename,
            row=dummy_row,
            line=2,
        )
        self.assertIsInstance(created_asset, ParentAsset)
        self.assertIsNone(created_asset.props)
        self.assertEqual(created_asset.parent, expected_parent)
        self.assertEqual(created_asset.nodes, expected_nodes)

        # parent asset wit props
        asset_types = ["Database", "Schema", "Table", "Column"]
        asset_names = ["DB1", "SCH1", "T1", ""]
        created_asset = _create_asset(
            asset_types=asset_types,
            asset_names=asset_names,
            domain_id=domain_id,
            fullname=fullname,
            csv_file=self.filename,
            row=dummy_row,
            line=2,
        )
        self.assertIsInstance(created_asset, ParentAsset)
        self.assertIsInstance(created_asset.props, AssetProperties)
        self.assertEqual(created_asset.parent, expected_parent)
        self.assertEqual(created_asset.nodes, expected_nodes)
        self.assertEqual(created_asset.props, expected_properties)

        # invalid - no parent defined
        asset_types = ["Database", "Schema", "Table", "Column"]
        asset_names = ["DB1", "SCH1", "", ""]
        with self.assertRaises(InvalidCSVException):
            _create_asset(
                asset_types=asset_types,
                asset_names=asset_names,
                domain_id=domain_id,
                fullname=fullname,
                csv_file=self.filename,
                row=dummy_row,
                line=2,
            )

        # invalid - no nodes defined
        asset_types = ["Database", "Schema", "Table", "Column"]
        asset_names = ["", "", "T1", "COL1"]
        with self.assertRaises(InvalidCSVException):
            _create_asset(
                asset_types=asset_types,
                asset_names=asset_names,
                domain_id=domain_id,
                fullname=fullname,
                csv_file=self.filename,
                row=dummy_row,
                line=2,
            )

    def test_ingest_csv_files(self):
        ingest_csv_files(
            source_directory="./test_data/csv",
            custom_lineage_config=self.custom_lineage_config,
        )

        with open("./test_data/csv/metadata.json") as input_file:
            expected_metadata = json.load(input_file)
        with open("./test_data/csv/ingested/metadata.json") as input_file:
            generated_metadata = json.load(input_file)
        with open("./test_data/csv/lineage_v3.json") as input_file:
            expected_lineage = json.load(input_file)
        with open("./test_data/csv/ingested/lineage.json") as input_file:
            generated_lineage = json.load(input_file)

        # accodomate for random uuid in source code
        for lineage in generated_lineage:
            if lineage.get("source_code"):
                lineage["source_code"]["path"] = "source_codes/uuid.txt"

        self.assertEqual(expected_metadata, generated_metadata)
        self.assertEqual(expected_lineage, generated_lineage)

        # cleanup
        shutil.rmtree(
            "/Users/kristof.vancoillie/Source/custom-technical-lineage-examples/tests/test_data/csv/ingested",
            ignore_errors=True,
        )


if __name__ == "__main__":
    unittest.main()
