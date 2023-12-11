import argparse
import csv
from pathlib import Path
from typing import List, Optional, Union

from src.exceptions import InvalidCSVException
from src.helper import generate_json_files, generate_source_code
from src.models import (
    Asset,
    AssetProperties,
    AssetType,
    CustomLineageConfig,
    LeafAsset,
    Lineage,
    NodeAsset,
    ParentAsset,
    SourceCode,
    SourceCodeHighLight,
)


def _get_default_asset_types() -> List[AssetType]:
    column_type = AssetType(name="Column", uuid="00000000-0000-0000-0000-000000031008")
    table_type = AssetType(name="Table", uuid="00000000-0000-0000-0000-000000031007")
    schema_type = AssetType(name="Schema", uuid="00000000-0000-0000-0001-000400000002")
    database_type = AssetType(name="Database", uuid="00000000-0000-0000-0000-000000031006")
    system_type = AssetType(name="System", uuid="00000000-0000-0000-0000-000000031302")
    return [system_type, database_type, schema_type, table_type, column_type]


def _validate_header(headers: List[str], csv_file: Path) -> List[int]:
    index_fullname = [i for i, header in enumerate(headers) if header == "fullname"]
    if len(index_fullname) != 2:
        raise InvalidCSVException(f"The headers of the csv file {csv_file} do no match the required input.")

    # there should be at least 1 node, parent and leaf
    if index_fullname[0] < 3 or index_fullname[1] - index_fullname[0] < 5:
        raise InvalidCSVException(f"The headers of the csv file {csv_file} do no match the required input.")

    if headers[index_fullname[0] : index_fullname[0] + 2] + headers[index_fullname[1] :] != [
        "fullname",
        "domain_id",
        "fullname",
        "domain_id",
        "source_code",
        "highlights",
        "transformation_display_name",
    ]:
        raise InvalidCSVException(f"The headers of the csv file {csv_file} do no match the required input.")

    return index_fullname


def _create_asset(
    asset_types: List[str], asset_names: List[str], domain_id: str, fullname: str, csv_file: str, row: List[str]
) -> Union[ParentAsset, LeafAsset]:
    # Creating node asset
    nodes = []
    for asset_name, asset_type in zip(asset_names[:-2], asset_types[:-2]):
        if asset_name:
            nodes.append(Asset(name=asset_name, type=asset_type))
    if not nodes:
        raise InvalidCSVException(f"No nodes defined in {csv_file} in row {row}")
    nodes_asset = NodeAsset(nodes=nodes)

    # Creating the props when relevant
    if fullname and domain_id:
        props = AssetProperties(fullname=fullname, domain_id=domain_id)
    else:
        props = None

    # Creating parrent asset
    if not asset_names[-2]:
        raise InvalidCSVException(f"Parent asset not defined in {csv_file} in row {row}")
    parent_asset = ParentAsset(
        nodes=nodes_asset.nodes, parent=Asset(name=asset_names[-2], type=asset_types[-2]), props=props
    )

    # Creating leaf asset - optionally
    if asset_names[-1]:
        return LeafAsset(
            nodes=nodes_asset.nodes,
            parent=parent_asset.parent,
            leaf=Asset(name=asset_names[-1], type=asset_types[-1]),
            props=props,
        )

    return parent_asset


def _create_source_code(
    source_code_text: str, highlights: str, transformation_display_name: str, custom_lineage_config: CustomLineageConfig
) -> Optional[SourceCode]:
    if not source_code_text:
        return None

    if highlights:
        source_code_highlights = []
        for highlight in highlights.split(","):
            source_code_highlights.append(
                SourceCodeHighLight(start=highlight.split(":")[0][1:], len=highlight.split(":")[1][:-1])
            )
    else:
        source_code_highlights = None

    return generate_source_code(
        source_code_text=source_code_text,
        custom_lineage_config=custom_lineage_config,
        transformation_display_name=transformation_display_name,
        highlights=source_code_highlights,
    )


def ingest_csv_files(source_directory: str, custom_lineage_config: CustomLineageConfig) -> None:
    source_dir = Path(source_directory)

    # Verify source directory exists
    if not source_dir.exists():
        raise InvalidCSVException(
            f"Could not find {source_dir}, please make sure to provide a correct source directory."
        )

    # Extract csv files from source directory
    csv_files = [f for f in source_dir.iterdir() if f.is_file() and f.suffix == ".csv"]
    if not csv_files:
        raise InvalidCSVException(
            f"No csv files found in {source_dir}, please make sure to provide directory with csv files."
        )

    # Extract the lineage relationships from the csv files
    lineages = []
    for csv_file_to_ingest in csv_files:
        with open(csv_file_to_ingest, "r") as csv_file:
            csv_reader = csv.reader(
                csv_file,
            )
            headers = next(csv_reader)
            index_fullname = _validate_header(headers=headers, csv_file=csv_file_to_ingest)
            for row in csv_reader:
                if len(row) != len(headers):
                    raise InvalidCSVException(
                        f"Row {row} in file {csv_file} does not contain same amount of entries as the headers"
                    )

                src = _create_asset(
                    asset_types=headers[: index_fullname[0]],
                    asset_names=row[: index_fullname[0]],
                    fullname=row[index_fullname[0]],
                    domain_id=row[index_fullname[0] + 1],
                    csv_file=csv_file.name,
                    row=row,
                )
                trg = _create_asset(
                    asset_types=headers[index_fullname[0] + 2 : index_fullname[1]],
                    asset_names=row[index_fullname[0] + 2 : index_fullname[1]],
                    fullname=row[index_fullname[1]],
                    domain_id=row[index_fullname[1] + 1],
                    csv_file=csv_file.name,
                    row=row,
                )

                source_code_text, highlights, transformation_display_name = row[index_fullname[1] + 2 :]
                source_code = _create_source_code(
                    source_code_text=source_code_text,
                    highlights=highlights,
                    transformation_display_name=transformation_display_name,
                    custom_lineage_config=custom_lineage_config,
                )

                lineages.append(Lineage(src=src, trg=trg, source_code=source_code))

    generate_json_files(
        lineages=lineages, custom_lineage_config=custom_lineage_config, asset_types=_get_default_asset_types()
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", help="Source directory of the csv files")
    parser.add_argument(
        "target_directory", help="Target directory in which the files for batch custom lineage will be stored"
    )
    args = parser.parse_args()

    custom_lineage_config = CustomLineageConfig(
        application_name="custom-lineage-batch-csv-ingested",
        output_directory=args.target_directory,
        source_code_directory_name="source_codes",
    )

    ingest_csv_files(source_directory=args.source_directory, custom_lineage_config=custom_lineage_config)