import json
import logging
import urllib.parse
import uuid
from typing import List, Optional, Sequence, Union

import requests
from pydantic.json import pydantic_encoder
from requests.auth import HTTPBasicAuth
from urllib3.connection import NameResolutionError

from src.exceptions import CollibraAPIError, InvalidUUIDException, MissingInputExpection

from .models import (
    Asset,
    AssetFullnameDomain,
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
MAX_HTTP_RETRY = 5


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


def collect_assets_fullname(
    collibra_instance: str,
    username: str,
    password: str,
    type_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    name: Optional[str] = None,
) -> List[AssetFullnameDomain]:
    """
    Helper function that collect assets fullname from Collibra

    :param collibra_instance: Collibra instance name
    :type collibra_instance: str
    :param username: Collibra username
    :type username: str
    :param password: Collibra user's password
    :type password: str
    :param type_id: Optional parameter - Asset type ID
    :type type_id: str
    :param domain_id: Optional parameter - Collibra domain ID
    :type domain_id: str
    :param name: Optional parameter - Assets name
    :type name: str
    :returns: list of AssetFullnameDomain objects
    :rtype: list
    """

    def get_assets_fullname_from_collibra() -> List[AssetFullnameDomain]:
        fullnames = []
        auth = HTTPBasicAuth(username=username, password=password)
        cursor = urllib.parse.quote("")
        limit = 1000
        attempt = 1
        base_path = f"https://{collibra_instance}.collibra.com/rest/2.0/assets?limit={limit}"

        if domain_id:
            base_path = base_path + f"&domainId={domain_id}"
        if type_id:
            base_path = base_path + f"&typeIds={type_id}"
        if name:
            base_path = base_path + f"&name={urllib.parse.quote(name)}"

        while cursor is not None:
            query_path = base_path + f"&cursor={cursor}"
            try:
                logging.debug(f"Sending GET {query_path}")
                ret = requests.get(query_path, auth=auth)
            except NameResolutionError as e:
                raise e
            except Exception as e:
                logging.warning(f"GET {query_path} failed with\n{e}")
                attempt += 1
            else:
                if ret.status_code == 200:
                    logging.debug(f"Response received for GET {query_path}: {ret.status_code}")
                    attempt = 1
                    result = json.loads(ret.text)
                    cursor = result.get("nextCursor")
                    for entry in result.get("results", []):
                        fullname = entry.get("name")
                        domain = entry.get("domain", {}).get("id")
                        uuid = entry.get("id")
                        if not fullname or not domain or not uuid:
                            continue
                        fullnames.append(
                            AssetFullnameDomain(
                                fullname=fullname,
                                domain_id=domain,
                                uuid=uuid,
                            )
                        )

                elif ret.status_code >= 400 and ret.status_code < 500:
                    raise CollibraAPIError(f"GET {query_path} failed with {ret.status_code} {ret.text}")
                else:
                    logging.warning(f"attempt {attempt}/5 GET {query_path} failed with {ret.status_code} {ret.text}")
                    attempt += 1
            if attempt > MAX_HTTP_RETRY:
                raise CollibraAPIError(f"Failed to retrieve asset's fullname after {MAX_HTTP_RETRY} attempts")
        return fullnames

    def validate_inputs():
        if not domain_id and not type_id and not name:
            raise MissingInputExpection("At least one of the parameters must be provided: typeId, domainId or name")

        if type_id:
            try:
                uuid.UUID(type_id)
            except ValueError:
                raise InvalidUUIDException(f"Type Id {type_id} is not a valid UUID")

        if domain_id:
            try:
                uuid.UUID(domain_id)
            except ValueError:
                raise InvalidUUIDException(f"Domain Id {domain_id} is not a valid UUID")

    validate_inputs()
    return get_assets_fullname_from_collibra()
