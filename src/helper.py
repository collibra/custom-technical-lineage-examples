import json
import logging
import shutil
import urllib.parse
import uuid
from pathlib import Path
from typing import List, Optional, Sequence, TypeAlias, Union

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
AssetTypeSequence: TypeAlias = Sequence[Union[NodeAsset, ParentAsset, LeafAsset]]


def generate_json_files(
    lineages: List[Lineage],
    asset_types: List[AssetType],
    custom_lineage_config: CustomLineageConfig,
    assets: Optional[AssetTypeSequence] = None,
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
        json.dump([lineage.model_dump(exclude_none=True) for lineage in lineages], out_file, default=pydantic_encoder)

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

    :param source_code_text: Text to use as source code or path of a file to be used
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
    # in case of a file
    if Path(source_code_text).is_file():
        file_name = Path(source_code_text).name
        shutil.copy(source_code_text, custom_lineage_config.source_code_directory_path / file_name)
    else:
        # generate file name
        file_name = f"{str(uuid.uuid4())}.txt"
        with open(custom_lineage_config.source_code_directory_path / file_name, "w") as out_file:
            out_file.write(source_code_text)
    return SourceCode(
        path=f"{custom_lineage_config.source_code_directory_name}/{file_name}",
        highlights=highlights,
        transformation_display_name=transformation_display_name,
    )


def _http_get(url: str, auth: HTTPBasicAuth) -> requests.Response:
    attempt = 1
    while attempt <= MAX_HTTP_RETRY:
        try:
            logging.info(f"Sending GET {url}")
            ret = requests.get(url, auth=auth)
        except NameResolutionError as e:
            raise e
        except Exception as e:
            attempt += 1
            logging.warning(f"GET {url} failed with\n{e}")
        else:
            if ret.status_code >= 400 and ret.status_code < 500:
                raise CollibraAPIError(f"GET {url} failed with {ret.status_code} {ret.text}")
            elif ret.status_code == 200:
                logging.info(f"Response received for GET {url}: {ret.status_code}")
                return ret
            else:
                logging.warning(f"attempt {attempt}/5 GET {url} failed with {ret.status_code} {ret.text}")
                attempt += 1

    raise CollibraAPIError(f"Failed GET {url} after {MAX_HTTP_RETRY} attempts")


def collect_assets_typeid(
    collibra_instance: str, username: str, password: str, asset_type: Optional[str] = None
) -> List[AssetType]:
    """
    Helper function that collect asset types ID from Collibra

    :param collibra_instance: Collibra instance name
    :type collibra_instance: str
    :param username: Collibra username
    :type username: str
    :param password: Collibra user's password
    :type password: str
    :param asset_type: Optional parameter - Asset type name
    :type asset_type: str
    :returns: list of AssetFullnameDomain objects
    :rtype: list
    """

    asset_types = []
    limit = 100
    offset = 0
    auth = HTTPBasicAuth(username=username, password=password)
    total = 1
    while offset < total:
        url = f"https://{collibra_instance}.collibra.com/rest/2.0/assetTypes?limit={limit}&offset={offset}"
        search_by_name = "" if not asset_type else f"&name={asset_type}&nameMatchMode=EXACT"
        ret = _http_get(url=f"{url}{search_by_name}", auth=auth)
        result = json.loads(ret.text)
        total = result["total"]
        offset += limit
        for entry in result["results"]:
            name = entry.get("name")
            id = entry.get("id")
            asset_types.append(AssetType(name=name, uuid=id))

    return asset_types


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
        base_path = f"https://{collibra_instance}.collibra.com/rest/2.0/assets?limit={limit}"

        if domain_id:
            base_path = base_path + f"&domainId={domain_id}"
        if type_id:
            base_path = base_path + f"&typeIds={type_id}"
        if name:
            base_path = base_path + f"&name={urllib.parse.quote(name)}"

        while cursor is not None:
            query_path = base_path + f"&cursor={cursor}"
            ret = _http_get(url=query_path, auth=auth)
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

        return fullnames

    def validate_inputs() -> None:
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


def get_asset_types_name_from_lineage_json_file(path: str) -> set:
    types = set()
    with open(path) as f:
        lineages = json.load(f)
        for lineage in lineages:
            for src_trg in ["src", "trg"]:
                types.add(lineage[src_trg].get("leaf", {}).get("type"))
                types.add(lineage[src_trg].get("parent", {}).get("type"))
                for node in lineage[src_trg].get("nodes", []):
                    types.add(node.get("type"))
    if None in types:
        types.remove(None)
    return types


def synchronize_capability(
    collibra_instance: str, username: str, password: str, capability_id: str
) -> Optional[requests.Response]:
    """
    Helper function that triggers the synchronisation of the custom lineage capability

    :param collibra_instance: Collibra instance name
    :type collibra_instance: str
    :param username: Collibra username
    :type username: str
    :param password: Collibra user's password
    :type password: str
    :param capability_id: ID of the capability to synchronize
    :type type_id: str
    :returns: response of the http post call to synchronize the capability
    :rtype: requests.Response
    """
    auth = HTTPBasicAuth(username=username, password=password)
    url = f"https://{collibra_instance}/rest/catalog/1.0/genericIntegration/{capability_id}/run"
    logging.info(f"Sending POST {url}")
    try:
        ret = requests.post(url=url, auth=auth)
    except NameResolutionError as e:
        raise e
    except Exception as e:
        logging.warning(f"POST {url} failed with\n{e}")
    else:
        if ret.status_code >= 400 and ret.status_code < 500:
            raise CollibraAPIError(f"POST {url} failed with {ret.status_code} {ret.text}")
        elif ret.status_code == 200:
            logging.info(f"Response received for GET {url}: {ret.status_code}")
            return ret
    return None
