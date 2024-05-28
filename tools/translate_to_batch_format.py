import argparse
import json
import os
from typing import Dict, List, Optional

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


def _convert_asset_hierarchy(asset_hierarchy: dict, nodes: Optional[List[Asset]] = None) -> List[LeafAsset]:
    nodes = nodes if nodes else []
    if "children" in asset_hierarchy:
        nodes.append(Asset(name=asset_hierarchy["name"], type=asset_hierarchy["type"]))
        for child in asset_hierarchy["children"]:
            return _convert_asset_hierarchy(asset_hierarchy=child, nodes=nodes)
    leaf_assets = []
    if "leaves" in asset_hierarchy:
        for leaf in asset_hierarchy["leaves"]:
            leaf_assets.append(
                LeafAsset(
                    nodes=nodes,
                    parent=Asset(name=asset_hierarchy["name"], type=asset_hierarchy["type"]),
                    leaf=Asset(name=leaf["name"], type=leaf["type"]),
                )
            )
    return leaf_assets


def convert_tree(tree_v1: List[dict]) -> List[LeafAsset]:
    leaf_assets = []
    for asset_hierarchy in tree_v1:
        leaf_assets.extend(_convert_asset_hierarchy(asset_hierarchy=asset_hierarchy))
    return leaf_assets


def _convert_lineage_source(
    lineage_relationship_v1: dict,
    codebase_files_v1: Dict[str, dict],
    custom_lineage_config: CustomLineageConfig,
    input_directory: str,
) -> Optional[SourceCode]:
    # simple custom technical lineage v1
    if "source_code" in lineage_relationship_v1:
        source_code_text = lineage_relationship_v1.get("source_code", "")
        mapping = lineage_relationship_v1.get("mapping", "")
        if not source_code_text and not mapping:
            return None

        return generate_source_code(
            source_code_text=source_code_text,
            custom_lineage_config=custom_lineage_config,
            transformation_display_name=mapping,
        )

    # advanced custom technical lineage v1
    if "mapping_ref" in lineage_relationship_v1:
        source_code_file_v1 = lineage_relationship_v1.get("mapping_ref", {}).get("source_code", "")
        mapping_v1 = lineage_relationship_v1.get("mapping_ref", {}).get("mapping", "")
        codebase_pos_v1 = lineage_relationship_v1.get("mapping_ref", {}).get("codebase_pos", [])
        if not source_code_file_v1:
            return None

        pos_start = (
            codebase_files_v1.get(source_code_file_v1, {})
            .get("mapping_refs", {})
            .get(mapping_v1, {})
            .get("pos_start", 0)
        )
        pos_len = (
            codebase_files_v1.get(source_code_file_v1, {}).get("mapping_refs", {}).get(mapping_v1, {}).get("pos_len", 0)
        )

        try:
            with open(os.path.join(input_directory, source_code_file_v1)) as source_code_file_v1_file:
                return generate_source_code(
                    source_code_text=source_code_file_v1_file.read()[pos_start : pos_start + pos_len],
                    custom_lineage_config=custom_lineage_config,
                    transformation_display_name=mapping_v1,
                    highlights=[
                        SourceCodeHighLight(start=highlight_v1["pos_start"], len=highlight_v1["pos_len"])
                        for highlight_v1 in codebase_pos_v1
                    ],
                )
        except FileNotFoundError as e:
            print(
                f"Could not find {source_code_file_v1} which is specified in your lineage.json file in \
                    the input directory: {input_directory}. Make sure all the referenced files are available."
            )
            raise e

    return None


def _convert_lineage_node(lineage_node: List[Dict[str, str]]) -> LeafAsset:
    nodes = []
    for asset_dict in lineage_node:
        for asset_type, asset_name in asset_dict.items():
            if asset_type.lower() == "column":
                leaf = Asset(name=asset_name, type=asset_type.title())
            elif asset_type.lower() == "table":
                parent = Asset(name=asset_name, type=asset_type.title())
            else:
                nodes.append(Asset(name=asset_name, type=asset_type.title()))

    return LeafAsset(nodes=nodes, parent=parent, leaf=leaf)


def convert_lineages(
    lineage_v1: List[dict],
    codebase_files_v1: Dict[str, dict],
    custom_lineage_config: CustomLineageConfig,
    migrate_source_code: bool,
    input_directory: str,
) -> List[Lineage]:
    lineage_batch: List[Lineage] = []
    for lineage_relationship_v1 in lineage_v1:
        # lineage relationship
        lineage_relationship = Lineage(
            src=_convert_lineage_node(lineage_relationship_v1["src_path"]),
            trg=_convert_lineage_node(lineage_relationship_v1["trg_path"]),
        )
        # source code
        if migrate_source_code:
            source_code = _convert_lineage_source(
                lineage_relationship_v1=lineage_relationship_v1,
                codebase_files_v1=codebase_files_v1,
                custom_lineage_config=custom_lineage_config,
                input_directory=input_directory,
            )
            if source_code:
                lineage_relationship.source_code = source_code

        # adding the lineage relationship and source code
        lineage_batch.append(lineage_relationship)

    return lineage_batch


def convert(input_directory: str, output_directory: str, migrate_source_code: bool) -> None:
    """
    Main function that converts custom lineage v1 format into batch custom lineage format (v3).
    """

    # input directory should contain lineage.json file to be converted
    lineage_v1_json = os.path.join(input_directory, "lineage.json")
    try:
        with open(lineage_v1_json) as f:
            custom_lineage = json.load(f)
    except FileNotFoundError:
        print(f"Could not find lineage.json in the input directory: {input_directory}")
        return

    custom_lineage_config = CustomLineageConfig(
        application_name="custom-lineage-batch-converted",
        output_directory=output_directory,
        source_code_directory_name="source_codes",
    )

    # Generate asset types
    column_type = AssetType(name="Column", uuid="00000000-0000-0000-0000-000000031008")
    table_type = AssetType(name="Table", uuid="00000000-0000-0000-0000-000000031007")
    schema_type = AssetType(name="Schema", uuid="00000000-0000-0000-0001-000400000002")
    database_type = AssetType(name="Database", uuid="00000000-0000-0000-0000-000000031006")
    system_type = AssetType(name="System", uuid="00000000-0000-0000-0000-000000031302")
    asset_types = [system_type, database_type, schema_type, table_type, column_type]

    # creating the assets
    leaf_assets = convert_tree(custom_lineage.get("tree", []))

    # creating the lineage relationships
    lineage_batch = convert_lineages(
        lineage_v1=custom_lineage.get("lineages", []),
        codebase_files_v1=custom_lineage.get("codebase_files", {}),
        custom_lineage_config=custom_lineage_config,
        migrate_source_code=migrate_source_code,
        input_directory=input_directory,
    )

    # creating the json files
    generate_json_files(
        assets=leaf_assets, lineages=lineage_batch, custom_lineage_config=custom_lineage_config, asset_types=asset_types
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", help="Source directory of the lineage.json file used for v1")
    parser.add_argument(
        "target_directory", help="Target directory in which the files for batch custom lineage will be stored"
    )
    parser.add_argument(
        "--migrate_source_code",
        action=argparse.BooleanOptionalAction,
        help="Option indicating whether source_code and mapping should be migrated or not",
    )
    args = parser.parse_args()
    convert(
        input_directory=args.source_directory,
        output_directory=args.target_directory,
        migrate_source_code=args.migrate_source_code,
    )
