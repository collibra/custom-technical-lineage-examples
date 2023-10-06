from src.helper import *
from src.models import *

# Providing general configuration
custom_lineage_config = CustomLineageConfig(
    application_name="custom-lineage-example-with-props",
    output_directory="/tmp/example_with_props",
    source_code_directory_name="source_codes",
)

# Generate asset types
column_type = AssetType(name="Column", uuid="00000000-0000-0000-0000-000000031008")
table_type = AssetType(name="Table", uuid="00000000-0000-0000-0000-000000031007")
schema_type = AssetType(name="Schema", uuid="00000000-0000-0000-0001-000400000002")
database_type = AssetType(name="Database", uuid="00000000-0000-0000-0000-000000031006")
system_type = AssetType(name="System", uuid="00000000-0000-0000-0000-000000031302")
directory_type = AssetType(name="Directory", uuid="00000000-0000-0000-0000-000000031303")
gcs_bucket_type = AssetType(name="GCS Bucket", uuid="00000000-0000-0000-0001-002700000002")
gcs_file_system_type = AssetType(name="GCS File System", uuid="00000000-0000-0000-0001-002700000001")
file_group_type = AssetType(name="File Group", uuid="00000000-0000-0000-0001-002400000002")

asset_types = [
    system_type,
    database_type,
    schema_type,
    table_type,
    column_type,
    directory_type,
    gcs_bucket_type,
    gcs_file_system_type,
    file_group_type,
]

# Creating common node asset
schema_node_asset = NodeAsset(
    nodes=[
        Asset(name="SYS1", type=system_type.name),
        Asset(name="DB1", type=database_type.name),
        Asset(name="SCH1", type=schema_type.name),
    ]
)

# Creating table
table_asset_1 = ParentAsset(nodes=schema_node_asset.nodes, parent=Asset(name="Table1", type=table_type.name))

# Creating the columns
table_columns = []
for column_number in range(1, 3):
    table_columns.append(
        LeafAsset(
            nodes=schema_node_asset.nodes,
            parent=table_asset_1.parent,
            leaf=Asset(name=f"Col{column_number}", type=column_type.name),
        )
    )

# Creating the assets
file_group_node_asset = NodeAsset(
    nodes=[
        Asset(name="gcs", type=gcs_file_system_type.name),
        Asset(name="catingestiontest", type=gcs_bucket_type.name),
        Asset(name="/", type=directory_type.name),
        Asset(name="CoETest", type=directory_type.name),
        Asset(name="coetest", type=file_group_type.name),
    ]
)
file_parent_asset = ParentAsset(
    nodes=file_group_node_asset.nodes,
    parent=Asset(name="coetest", type=table_type.name),
    props=AssetProperties(
        fullname="<gcs_id> > projects/<project_id>/locations/us-east1/lakes/lake-in-us-east1/zones/raw/entities/coetest",
        domain_id="<domain_id>",
    ),
)
file_leaf_asset_first_name = LeafAsset(
    nodes=file_group_node_asset.nodes,
    parent=file_parent_asset.parent,
    leaf=Asset(name="first_name", type=column_type.name),
    props=AssetProperties(
        fullname="<gcs_id> > projects/<project_id>/locations/us-east1/lakes/lake-in-us-east1/zones/raw/entities/coetest > first_name",
        domain_id="<domain_id>",
    ),
)
file_leaf_asset_last_name = LeafAsset(
    nodes=file_group_node_asset.nodes,
    parent=file_parent_asset.parent,
    leaf=Asset(name="last_name", type=column_type.name),
    props=AssetProperties(
        fullname="<gcs_id> > projects/<project_id>/locations/us-east1/lakes/lake-in-us-east1/zones/raw/entities/coetest > last_name",
        domain_id="<domain_id>",
    ),
)
assets = [file_parent_asset]


# Creating direct lineage relations
lineages = []
for src, trg in zip(table_columns, [file_leaf_asset_first_name, file_leaf_asset_last_name]):
    lineages.append(
        Lineage(
            src=src,
            trg=trg,
        )
    )

# Generating the json files
generate_json_files(
    assets=assets, lineages=lineages, asset_types=asset_types, custom_lineage_config=custom_lineage_config
)
