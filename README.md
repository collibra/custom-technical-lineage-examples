# Custom technical lineage

This repository contains examples and helper functions to develop custom technical lineage files.

## Conversion tool from V1 to batch format

Usage:
```python3 -m tools.translate_to_batch_format <source_directory> <target_directory> [--migrate_source_code]```

Where:
 * `<source_directory>` is an existing directory with custom technical lineage v1 files.
 * `<target_directory>` is a target directory for custom technical lineage batch format artifacts. Target directory will be created if it does not exist.
 * `--migrate_source_code` is an optional flag to invoke extraction of source codes as well.


## Convert CSV files into custom technical lineage batch format

Usage:
```python3 -m tools.ingest_csv <source_directory> <target_directory>```

Where:
 * `<source_directory>` is an existing directory with csv files to be translated into custom technical lineage batch format.
 * `<target_directory>` is a target directory for custom technical lineage batch format artifacts. Target directory will be created if it does not exist.

The first row in every csv file is the header, the following rows define the lineage relationships. If we take a look at an example header row we find in order:
```csv
System,Database,Schema,Table,Column,fullname,domain_id,System,Database,Schema,Table,Column,fullname,domain_id,source_code,highlights,transformation_display_name
```
 * `System`, `Database`, `Schema` define the asset types for the nodes of the source, you must have at least 1 node but can have as many as you want
 * `Table` is the asset type of the parent asset of the source, this header is mandatory
 * `Column` is the asset type of the leaf asset of the source, this header is mandatory
 * `fullname` and `domain_id` are mandatory headers in case a custom `fullname` and `domain_id` must be provided for the source
 * `System`, `Database`, `Schema` define the asset types for the nodes of the target, you must have at least 1 node but can have as many as you want
 * `Table` is the asset type of the parent asset of the target, this header is mandatory
 * `Column` is the asset type of the leaf asset of the target, this header is mandatory
 * `fullname` and `domain_id` are mandatory headers in case a custom `fullname` and `domain_id` must be provided for the target
 * `source_code`, `highlights` and `transformation_display_name` are mandatory headers

 When providing the lineage relationships keep the following in mind:

 * value for the node and parent asset type is mandatory for both source and target
 * value for the leaf asset type is optional
 * values for `fullname` and `domain_id` are optional
 * values for `source_code`, `highlights` and `transformation_display_name` are optional
 * `source_code` can be either a string or a full path to a file

 As the headers define the asset types you define the lineage relationships for, this means that 1 file can only contain lineage relationships for the same type of assets in the source/target, you can however create as many csv files in the directory as you want. The generated `metadata.json` file will contain the definition for `System`, `Database`, `Schema`, `Table` and `Column`; if you are using any other asset types you will need to add these in the `metadata.json` file with their respective `uuid`.
 
 Let's have a look at two examples:

### CSV Example 1

 ```
 System,Database,Schema,Table,Column,fullname,domain_id,System,Database,Schema,Table,Column,fullname,domain_id,source_code,highlights,transformation_display_name
snowflake,KRISTOF,PUBLIC,T1,USERID,,,snowflake,KRISTOF,PUBLIC,V2,UI_2L,,,CREATE VIEW KRISTOF.PUBLIC.V2 AS select USERID from KRISTOF.PUBLIC.T1,"[0:70]",transformation
snowflake,KRISTOF,PUBLIC,T2,,domain1,,,KRISTOF,PUBLIC,V2,,,,,,
 ```

 The first row defines column level lineage and provides details about the `source_code`, `highlights` and `transformation_display_name`, the 2nd row defines table level lineage.

 ### CSV Example 2

 ```
 GCS File System,GCS Bucket,Directory,Directory,File,fullname,domain_id,System,Database,Schema,Table,Column,fullname,domain_id,source_code,highlights,transformation_display_name
gcs,catingestiontest,/,ingestion-test,mytest.csv,f13bf705-13a4-44c9-843e-f341feccfb6e > catingestiontest/ingestion-test/ingestion copy/mytest.csv/1611609340099809,fea1b0b0-705f-4e0d-b5eb-1f21132cc718,snowflake,KRISTOF,PUBLIC,V2,UI_2L,,,snowflake data pipline abc,,transformation
 ```

Thix example creates a lineage relationship between a file and a column, for the file the custom `fullname` and `domain_id` are provided as this is required for stitching.

## Python custom technical lineage batch version examples

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