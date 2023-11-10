import requests
import urllib.parse
import json
from argparse import ArgumentParser
from uuid import UUID
from requests.auth import HTTPBasicAuth
from typing import List

def get_assets_fullname(collibra_instance: str, username: str, password: str,
                        typeId: str=None, domainId:str=None, name:str=None) -> List:
    fullnames = []
    auth = HTTPBasicAuth(username=username, password=password)
    cursor = urllib.parse.quote('')
    limit = 1000
    retry = 0
    base_path = f'https://{collibra_instance}.collibra.com/rest/2.0/assets?limit={limit}'

    if domainId:
        base_path = base_path + f'&domainId={domainId}'
    if typeId:
        base_path = base_path + f'&typeIds={typeId}'
    if name:
        base_path = base_path + f'&name={urllib.parse.quote(name)}'

    while cursor is not None and retry < 5:
        query_path = base_path + f'&cursor={cursor}'
        try:
            print(f'Sending GET {query_path}')
            ret = requests.get(query_path, auth=auth)
        except Exception as e:
            print(f'GET {query_path} failed with\n{e}')
            retry += 1
        else:
            if ret.status_code == 200:
                print(f'Response received for GET {query_path}: {ret.status_code}')
                retry = 0
                result = json.loads(ret.text)
                cursor = result['nextCursor'] if 'nextCursor' in result else None
                for entry in result['results']:
                    fullnames.append({"fullname" : entry.get('name', ''),
                                      "domain ID": entry.get('domain', {}).get('id', ''),
                                      "id": entry.get('id', '')})

            elif ret.status_code >= 400 and ret.status_code < 500:
                print(f'GET {query_path} failed with {ret.status_code} {ret.text}')
                exit()
            else:
                print(f'GET {query_path} failed with {ret.status_code} {ret.text}')
                retry += 1

    if retry == 5:
        print("Failed to retrieve asset's fullname")
        exit()
    return fullnames

def is_valid_uuid(uuid_input: str) -> bool:
    try:
        UUID(uuid_input)
    except:
        return False
    return True

def wrong_uuid_message(input_type: str, uuid: str) -> str:
    return f"The {input_type} entered {args.domainId} is not a valid ID"

def write_result_to_file(fullnames: list):
    with open('result.json', 'w') as f:
        json.dump(fullnames, f, indent=4)



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-c', '--collibraInstance')
    parser.add_argument('-u', '--username')
    parser.add_argument('-p', '--password')
    parser.add_argument('-d', '--domainId')
    parser.add_argument('-t', '--typeId')
    parser.add_argument('-n', '--name')

    args = parser.parse_args()
    collibra_instance = args.collibraInstance
    username = args.username
    password = args.password
    domainId = args.domainId
    typeId = args.typeId
    name = args.name
    print(domainId, typeId, name)
    if not collibra_instance or not username or not password:
        print('The COLLIBRAINSTANCE, USERNAME and PASSWORD parameters are mandatory')
        print('for help: python collect_assets_fullname.py -h')
        exit()
    if not domainId and not typeId and not name:
        print('It is mandatory to specify one of those parameters: DOMAINID, TYPEID, NAME')
        exit()
    if args.domainId:
        if not is_valid_uuid(args.domainId):
            print(wrong_uuid_message('domain ID', args.domainId))
            exit()
    if args.typeId:
        if not is_valid_uuid(args.typeId):
            print(wrong_uuid_message('type ID', args.domainId))
            exit()

    fullnames = get_assets_fullname(collibra_instance=collibra_instance,
                        username=username,
                        password=password,
                        domainId=domainId,
                        typeId=typeId,
                        name=name)
    write_result_to_file(fullnames)

