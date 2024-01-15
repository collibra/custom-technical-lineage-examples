import json
from argparse import ArgumentParser

from pydantic.json import pydantic_encoder

from src.helper import collect_assets_typeid


def write_result_to_file(asset_types: dict) -> None:
    with open("metadata.json", "w") as f:
        json.dump(asset_types, f, indent=4, default=pydantic_encoder)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c",
        "--collibraInstance",
        help="Collibra instance name. If your URL is "
        "https://mysintance.collibra.com, "
        "the instance name is 'mysintance'",
    )
    parser.add_argument("-u", "--username", help="Collibra account's username used fetch the asset type IDs")
    parser.add_argument("-p", "--password", help="Collibra account's password used fetch the asset type IDs")
    parser.add_argument(
        "-a", "--applicationName", help="The type of data source for which " "you are creating a technical lineage."
    )
    parser.add_argument("-t", "--assetType", help="Name of the asset for which the ID needs to be retrieved")

    args = parser.parse_args()
    collibra_instance = args.collibraInstance
    username = args.username
    password = args.password
    application_name = args.applicationName
    asset_type = args.assetType
    result = {"application_name": application_name, "version": "3", "asset_types": {}}
    asset_types = collect_assets_typeid(
        collibra_instance=collibra_instance, username=username, password=password, asset_type=asset_type
    )
    for asset_type in asset_types:
        result["asset_types"][asset_type.name] = {"uuid": asset_type.uuid}
    write_result_to_file(result)
