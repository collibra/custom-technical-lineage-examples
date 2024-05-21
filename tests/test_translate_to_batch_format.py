import json
import shutil

from tools.translate_to_batch_format import convert

def test_translate_with_simple_and_advanced_source_code() -> None:
    convert(
        input_directory="./test_data/conversion",
        output_directory="./test_data/conversion/v3",
        migrate_source_code=True,
    )

    # compare converted with expected
    with open("./test_data/conversion/metadata.json") as input_file:
        expected_metadata = json.load(input_file)

    with open("./test_data/conversion/v3/metadata.json") as input_file:
        generated_metadata = json.load(input_file)

    with open("./test_data/conversion/lineage_v3.json") as input_file:
        expected_lineage = json.load(input_file)

    with open("./test_data/conversion/v3/lineage.json") as input_file:
        generated_lineage = json.load(input_file)

    for lineage in generated_lineage:
        if lineage.get("source_code"):
            lineage["source_code"]["path"] = "source_codes/uuid.txt"

    assert expected_metadata == generated_metadata
    assert expected_lineage == generated_lineage

    # cleanup
    shutil.rmtree("./test_data/conversion/v3", ignore_errors=True)

def test_translat_without_source_code() -> None:
    # convert input
    convert(
        input_directory="./test_data/conversion",
        output_directory="./test_data/conversion/v3",
        migrate_source_code=False,
    )

    # compare converted with expected
    with open("./test_data/conversion/metadata.json") as input_file:
        expected_metadata = json.load(input_file)

    with open("./test_data/conversion/v3/metadata.json") as input_file:
        generated_metadata = json.load(input_file)

    with open("./test_data/conversion/lineage_v3_no_source_code.json") as input_file:
        expected_lineage = json.load(input_file)

    with open("./test_data/conversion/v3/lineage.json") as input_file:
        generated_lineage = json.load(input_file)

    assert expected_metadata == generated_metadata
    assert expected_lineage == generated_lineage

    # cleanup
    shutil.rmtree("./test_data/conversion/v3", ignore_errors=True)
