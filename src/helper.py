import json
import uuid
from typing import List, Optional, Sequence, Union

from pydantic.json import pydantic_encoder

from .models import (
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

__all__ = ["generate_json_files", "generate_source_code"]


def generate_json_files(
    assets: Sequence[Union[NodeAsset, ParentAsset, LeafAsset]],
    lineages: List[Lineage],
    asset_types: List[AssetType],
    custom_lineage_config: CustomLineageConfig,
) -> None:
    """
    Helper function that generates the json files which can be used as input for custom technical lineage batch format

    :param assets: List of assets which will be used to construct assets.json file
    :type assets: Sequence[Union[NodeAsset, ParentAsset, LeafAsset]]
    :param lineages: List of lineage relationships which will be used to construct lineage.json
    :type lineages: List[Lineage]
    :param asset_types: List of asset types which will be used to construct metadata.json file
    :type asset_types: List[AssetType]
    :param custom_lineage_config: Configuration object
    :type custom_lineage_config: CustomLineageConfig
    :returns: nothing
    :rtype: None
    """
    # creating assets.json
    if assets:
        with open(custom_lineage_config.output_directory_path / "assets.json", "w") as out_file:
            json.dump(assets, out_file, default=pydantic_encoder)

    # creating lineage.json
    with open(custom_lineage_config.output_directory_path / "lineage.json", "w") as out_file:
        json.dump(lineages, out_file, default=pydantic_encoder)

    # creating metadata.json
    with open(custom_lineage_config.output_directory_path / "metadata.json", "w") as out_file:
        metadata = {
            "version": 3,
            "application_name": custom_lineage_config.application_name,
            "asset_types": {asset_type.name: {"uuid": asset_type.uuid} for asset_type in asset_types},
        }
        json.dump(metadata, out_file)


def generate_source_code(
    source_code_text: str,
    custom_lineage_config: CustomLineageConfig,
    highlights: Optional[List[SourceCodeHighLight]] = None,
    transformation_display_name: Optional[str] = None,
) -> SourceCode:
    """
    Helper function that generates `SourceCode` object.

    :param source_code_text: Text to use as source code
    :type source_code_text: str
    :param custom_lineage_config: Configuration object
    :type custom_lineage_config: CustomLineageConfig
    :param highlights: List of SourceCodeHighLight objects
    :type highlights: List[SourceCodeHighLight], optional
    :param transformation_display_name: Text to use as transformation name
    :type transformation_display_name: str
    :returns: SourceCode object constructed using the provided input
    :rtype: SourceCode
    """
    # generate file name and create directory
    file_name = f"{str(uuid.uuid4())}.txt"
    with open(custom_lineage_config.source_code_directory_path / file_name, "w") as out_file:
        out_file.write(source_code_text)
    return SourceCode(
        path=f"{custom_lineage_config.source_code_directory_name}/{file_name}",
        highlights=highlights,
        transformation_display_name=transformation_display_name,
    )
