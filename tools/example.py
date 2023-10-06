from src.helper import *
from src.models import *

# Providing general configuration
custom_lineage_config = CustomLineageConfig(
    application_name="custom-lineage-basic-demo",
    output_directory="/Users/kristof.vancoillie/Documents/Collibra/Custom Lineage/sdk/basic",
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
