import json
import logging
from argparse import ArgumentParser

from src.helper import collect_assets_fullname

logger = logging.getLogger(__name__)


def write_result_to_file(fullnames: list):
    with open("result.json", "w") as f:
        json.dump(fullnames, f, indent=4)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--collibraInstance")
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    parser.add_argument("-d", "--domainId")
    parser.add_argument("-t", "--typeId")
    parser.add_argument("-n", "--name")

    args = parser.parse_args()
    collibra_instance = args.collibraInstance
    username = args.username
    password = args.password
    domain_id = args.domainId
    type_id = args.typeId
    name = args.name
    print(f"Input:\n\t- domain Id: {domain_id},\n\t- type Id: {type_id},\n\t- name: {name}")
    fullnames = collect_assets_fullname(
        collibra_instance=collibra_instance,
        username=username,
        password=password,
        domain_id=domain_id,
        type_id=type_id,
        name=name,
    )

    print("Collectin fullnames done. Writing result to file")
    write_result_to_file(fullnames)
