# Custom technical lineage

This repository contains examples and helper functions to help you develop your custom technical lineage files.

## Convert single-file definition files to the new batch definition format

Usage:
```python3 -m tools.translate_to_batch_format <source_directory> <target_directory> [--migrate_source_code]```

Where:
 * `<source_directory>` is the existing directory with the single-file definition files that you want to convert.
 * `<target_directory>` is the target directory for the resulting batch definition artifacts. If the target directory doesn't exist, it will be created.
 * `--migrate_source_code` is an optional element that extracts the source code.


## Convert CSV files to the new batch definition format

Usage:
```python3 -m tools.ingest_csv <source_directory> <target_directory>```

Where:
 * `<source_directory>` is the existing directory with the CSV files that you want to convert.
 * `<target_directory>` is the target directory for the resulting batch definition artifacts. If the target directory doesn't exist, it will be created.

The first row in every CSV file is the header. The following rows define the lineage relationships. If we take a look at an example header row, we find in order:
```csv
System,Database,Schema,Table,Column,fullname,domain_id,System,Database,Schema,Table,Column,fullname,domain_id,source_code,highlights,transformation_display_name
```
 * `System`, `Database`, and `Schema` define the asset types for the nodes of the source. You can have as many nodes as you want, but you must have a least one.
 * `Table` is the asset type of the parent asset of the source. This header is mandatory.
 * `Column` is the asset type of the leaf asset of the source. This header is mandatory.
 * `fullname` and `domain_id` are mandatory headers in cases where a custom `fullname` and `domain_id` must be provided for the source.
 * `System`, `Database`, and `Schema` define the asset types for the nodes of the target. You can have as many nodes as you want, but you must have a least one.
 * `Table` is the asset type of the parent asset of the target. This header is mandatory.
 * `Column` is the asset type of the leaf asset of the target. This header is mandatory.
 * `fullname` and `domain_id` are mandatory headers in cases where a custom `fullname` and `domain_id` must be provided for the target.
 * `source_code`, `highlights`, and `transformation_display_name` are mandatory headers.

 When providing the lineage relationships, keep the following in mind:

 * Values for the node and parent asset types are mandatory for both the source and the target.
 * A value for the leaf asset type is optional.
 * Values for `fullname` and `domain_id` are optional.
 * Values for `source_code`, `highlights`, and `transformation_display_name` are optional.
 * `source_code` can either be a string or the full path to a file.

Headers define the asset types for which you define the lineage relationships; therefore, one file can only contain lineage relationships for the same type of assets in the source/target. You can, however, create as many CSV files as you want in the directory. The generated `metadata.json` file will contain the definition for `System`, `Database`, `Schema`, `Table`, and `Column`. If you are using any other asset types, you need to add these in the `metadata.json` file, with their respective `uuid`.
 
Let's have a look at two examples:

### CSV Example 1

 ```
 System,Database,Schema,Table,Column,fullname,domain_id,System,Database,Schema,Table,Column,fullname,domain_id,source_code,highlights,transformation_display_name
snowflake,KRISTOF,PUBLIC,T1,USERID,,,snowflake,KRISTOF,PUBLIC,V2,UI_2L,,,CREATE VIEW KRISTOF.PUBLIC.V2 AS select USERID from KRISTOF.PUBLIC.T1,"[0:70]",transformation
snowflake,KRISTOF,PUBLIC,T2,,domain1,,,KRISTOF,PUBLIC,V2,,,,,,
 ```

The first row defines the column-level lineage and provides details about the `source_code`, `highlights` and `transformation_display_name`. The second row defines the table-level lineage.

 ### CSV Example 2

 ```
GCS File System,GCS Bucket,Directory,Directory,File,fullname,domain_id,System,Database,Schema,Table,Column,fullname,domain_id,source_code,highlights,transformation_display_name
gcs,catingestiontest,/,ingestion-test,mytest.csv,f13bf705-13a4-44c9-843e-f341feccfb6e > catingestiontest/ingestion-test/ingestion copy/mytest.csv/1611609340099809,fea1b0b0-705f-4e0d-b5eb-1f21132cc718,snowflake,KRISTOF,PUBLIC,V2,UI_2L,,,snowflake data pipline abc,,transformation
 ```

This example creates a lineage relationship between a file and a column. The custom `fullname` and `domain_id` are provided for the file because they are needed to obtain stitching.

## Python batch definition custom technical lineage examples

`tools.example.py` and `tools.example_with_props.py` contain examples of how you can use the models and helper functions defined in `src.models.py` and `src.helper.py`.

## Retrieve the fullname and domain ID of an asset, based on the domain ID, type ID or display name

Usage: 
```python3 -m tools.collect_assets_fullname [--collibraInstance] [--username] [--password] [--domainId] [--typeId] [--name]```

Where:
* `--collibraInstance` is the name of the Collibra environment. If, for example, the URL of the environment is `https://myinstance.collibra.com`, the environment name is `myinstance`.
* `--username` is the Collibra username used to make API calls.
* `--password` is the Collibra account password.
* `--domainId` is the domain ID of the relevant asset. This is optional.
* `--typeId` is the asset type ID of the relevant asset. This is optional.
* `--name` is the display name of the relevant asset. This is optional.

## License

Custom technical lineage examples are available under the [Collibra Marketplace License agreement](https://www.collibra.com/us/en/legal/documents/collibra-marketplace-license-agreement).
