from src.helper import collect_assets_typeid
import json
from pydantic.json import pydantic_encoder
from argparse import ArgumentParser

def write_result_to_file(asset_types: dict):
    with open("metadata.json", "w") as f:
        json.dump(asset_types, f, indent=4, default=pydantic_encoder)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--collibraInstance")
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    parser.add_argument("-a", "--applicationName")
    parser.add_argument("-t", "--assetType")


    args = parser.parse_args()
    collibra_instance = args.collibraInstance
    username = args.username
    password = args.password
    application_name = args.applicationName
    asset_type = args.assetType
    result = {"application_name": application_name,
              "version": "3",
              "asset_types": {}}
    asset_types = collect_assets_typeid(collibra_instance=collibra_instance, username=username, password=password,
                                        asset_type=asset_type)
    for asset_type in asset_types:
        result["asset_types"][asset_type.name] = {"uuid": asset_type.uuid}
    write_result_to_file(result)
