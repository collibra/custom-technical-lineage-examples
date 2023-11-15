import json
import uuid
import urllib.parse
import requests
from typing import List, Optional, Sequence, Union
from requests.auth import HTTPBasicAuth
from src.exceptions import *


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

def collect_assets_fullname(collibra_instance: str, username: str, password: str,
                        typeId: str=None, domainId:str=None, name:str=None) -> List:
    """
    Helper function that collect assets fullname from Collibra

    :param collibra_instance: Collibra instance name
    :type collibra_instance: str
    :param username: Collibra username
    :type username: str
    :param password: Collibra user's password
    :type password: str
    :param typeId: Optional parameter - Asset type ID
    :type typeId: str
    :param domainId: Optional parameter - Collibra domain ID
    :type domainId: str
    :param name: Optional parameter - Assets name
    :type name: str
    :returns: list of dictionary
    :rtype: list
    """

    def get_assets_fullname_from_collibra() -> List:
        fullnames = []
        auth = HTTPBasicAuth(username=username, password=password)
        cursor = urllib.parse.quote('')
        limit = 1000
        attempt = 1
        base_path = f'https://{collibra_instance}.collibra.com/rest/2.0/assets?limit={limit}'

        if domainId:
            base_path = base_path + f'&domainId={domainId}'
        if typeId:
            base_path = base_path + f'&typeIds={typeId}'
        if name:
            base_path = base_path + f'&name={urllib.parse.quote(name)}'

        while cursor is not None:
            query_path = base_path + f'&cursor={cursor}'
            try:
                print(f'Sending GET {query_path}')
                ret = requests.get(query_path, auth=auth)
            except Exception as e:
                print(f'GET {query_path} failed with\n{e}')
                attempt += 1
            else:
                if ret.status_code == 200:
                    print(f'Response received for GET {query_path}: {ret.status_code}')
                    attempt = 1
                    result = json.loads(ret.text)
                    cursor = result['nextCursor'] if 'nextCursor' in result else None
                    for entry in result['results']:
                        fullnames.append({"fullname": entry.get('name', ''),
                                          "domain ID": entry.get('domain', {}).get('id', ''),
                                          "id": entry.get('id', '')})

                elif ret.status_code >= 400 and ret.status_code < 500:
                    raise CollibraAPIError(f'GET {query_path} failed with {ret.status_code} {ret.text}')
                else:
                    print(f'attempt {attempt}/5 GET {query_path} failed with {ret.status_code} {ret.text} ')
                    attempt += 1
            if attempt > 5:
                raise CollibraAPIError(f"Failed to retrieve asset's fullname after 5 attempts")
        return fullnames
    def validate_inputs():
        if not domainId and not typeId and not name:
            raise MissingInputExpection(
                "At least one of the parameters must be provided: typeId, domainId or name")

        if typeId:
            try:
                uuid.UUID(typeId)
            except ValueError:
                raise InvalidUUIDException(f'{typeId} is not a valid UUID')

        if domainId:
            try:
                uuid.UUID(domainId)
            except ValueError:
                raise InvalidUUIDException(f'{domainId} is not a valid UUID')

    validate_inputs()
    return get_assets_fullname_from_collibra()
