# custom-technical-lineage-examples

This repository contains examples and helper functions to develop custom technical lineage files.

## Conversion tool from V1 to batch format

Usage:
```python3 -m tools.translate_to_batch_format <source_directory> <target_directory> [--migrate_source_code]```

Where:
 * `<source_directory>` is an existing directory with custom technical lineage v1 files.
 * `<target_directory>` is a target directory for custom technical lineage batch format artifacts. Target directory will be created if it does not exist.
 * `--migrate_source_code` is an optional flag to invoke extraction of source codes as well.

## Examples

`tools.example.py` and `tools.example_with_props.py` contain examples on how the models and helper functions defined in `src.models.py` and `src.helper.py` can be leveraged.

## Retrieve assets fullname and domain ID based on domain ID, type ID or display name

Usage: 
```python3 -m tools.collect_assets_fullname [--collibraInstance] [--username] [--password] [--domainId] [--typeId] [--name]```

Where:
* `--collibraInstance` is the Collibra instance name. If instance's URL is https://myinstance.collibra.com the instance name is myinstance
* `--username` is the Collibra username used to make API calls
* `--password` is the Collibra's account password
* `--domainId` optional: is the domain ID of the assets details to be retrieved
* `--typeId` optional: is the type ID of the assets details to be retrieved
* `--name` optional: is the display name of the asset's details to be retrieved

## License

Custom technical lineage examples is available under the [Collibra Marketplace License agreement](https://www.collibra.com/us/en/legal/documents/collibra-marketplace-license-agreement).