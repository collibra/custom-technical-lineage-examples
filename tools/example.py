from src.edge import EdgeConnection
from src.helper import generate_json_files, generate_source_code, synchronize_capability
from src.models import (
    Asset,
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

# Providing general configuration
custom_lineage_config = CustomLineageConfig(
    application_name="custom-lineage-example",
    output_directory="/tmp/example",
    source_code_directory_name="source_codes",
)

# Generate asset types
column_type = AssetType(name="Column", uuid="00000000-0000-0000-0000-000000031008")
table_type = AssetType(name="Table", uuid="00000000-0000-0000-0000-000000031007")
schema_type = AssetType(name="Schema", uuid="00000000-0000-0000-0001-000400000002")
database_type = AssetType(name="Database", uuid="00000000-0000-0000-0000-000000031006")
system_type = AssetType(name="System", uuid="00000000-0000-0000-0000-000000031302")
asset_types = [system_type, database_type, schema_type, table_type, column_type]

# Creating common node asset
schema_node_asset = NodeAsset(
    nodes=[
        Asset(name="SYS1", type=system_type.name),
        Asset(name="DB1", type=database_type.name),
        Asset(name="SCH1", type=schema_type.name),
    ]
)

# Creating tables and views
table_asset_1 = ParentAsset(nodes=schema_node_asset.nodes, parent=Asset(name="Table1", type=table_type.name))
view_asset_1 = ParentAsset(nodes=schema_node_asset.nodes, parent=Asset(name="View1", type=table_type.name))
table_asset_2 = ParentAsset(nodes=schema_node_asset.nodes, parent=Asset(name="Table2", type=table_type.name))
view_asset_2 = ParentAsset(nodes=schema_node_asset.nodes, parent=Asset(name="View2", type=table_type.name))

# Creating the columns
table_columns = []
view_columns = []
for column_number in range(1, 5):
    table_columns.append(
        LeafAsset(
            nodes=schema_node_asset.nodes,
            parent=table_asset_1.parent,
            leaf=Asset(name=f"Col{column_number}", type=column_type.name),
        )
    )
    view_columns.append(
        LeafAsset(
            nodes=schema_node_asset.nodes,
            parent=view_asset_1.parent,
            leaf=Asset(name=f"Col{column_number}", type=column_type.name),
        )
    )

# Creating direct lineage relations
lineages = []
for src, trg in zip(table_columns, view_columns):
    lineages.append(
        Lineage(
            src=src,
            trg=trg,
            source_code=SourceCode(
                path=f"{custom_lineage_config.source_code_directory_name}/source1.txt",
                highlights=[SourceCodeHighLight(start=1, len=100)],
                transformation_display_name="transformation_basic",
            ),
        )
    )

# Creating indirect lineage
lineages.append(
    Lineage(
        src=table_columns[0],
        trg=view_asset_1,
    )
)

# Creating table level lineage
lineages.append(
    Lineage(
        src=table_asset_2,
        trg=view_asset_2,
        source_code=generate_source_code(
            source_code_text="View 2 generated from Table 2",
            custom_lineage_config=custom_lineage_config,
            transformation_display_name="table_level_lineage_example",
        ),
    )
)

# Generating the json files
generate_json_files(assets=[], lineages=lineages, asset_types=asset_types, custom_lineage_config=custom_lineage_config)

# Preparing the Edge capability
edge_directory = "/tmp/cl3/"  # this is the folder on  Edge to which the files will be uploaded to
edge_shared_connection_folder = "shared-folder"  # this is the name of the shared folder as configured on the capability
edge_connection = EdgeConnection(address="192.169.10.10", username="username", certificate="/path-to-ssh-cert")
edge_connection.upload_folder(source_folder=custom_lineage_config.output_directory_path, target_folder=edge_directory)
edge_connection.upload_edge_shared_folder(
    edge_directory=edge_directory, shared_connection_folder=edge_shared_connection_folder
)

# Trigger the capability
synchronize_capability(
    collibra_instance="", username="Admin", password="password", capability_id="custom_lineage_capability_id"
)