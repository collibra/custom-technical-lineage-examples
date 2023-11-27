from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, model_validator

__all__ = [
    "Asset",
    "AssetType",
    "AssetProperties",
    "SourceCode",
    "SourceCodeHighLight",
    "NodeAsset",
    "ParentAsset",
    "LeafAsset",
    "Lineage",
    "CustomLineageConfig",
]


class AssetType(BaseModel):
    name: str
    uuid: str


class Asset(BaseModel):
    name: str
    type: str


class AssetProperties(BaseModel):
    fullname: str
    domain_id: str


class AssetFullnameDomain(BaseModel):
    fullname: str
    domain_id: str
    uuid: str


class SourceCodeHighLight(BaseModel):
    start: int
    len: int


class SourceCode(BaseModel):
    path: str
    highlights: Optional[List[SourceCodeHighLight]] = None
    transformation_display_name: Optional[str] = None


class NodeAsset(BaseModel):
    nodes: List[Asset]
    props: Optional[AssetProperties] = None


class ParentAsset(BaseModel):
    nodes: List[Asset]
    parent: Asset
    props: Optional[AssetProperties] = None


class LeafAsset(BaseModel):
    nodes: List[Asset]
    parent: Asset
    leaf: Asset
    props: Optional[AssetProperties] = None


class Lineage(BaseModel):
    src: Union[LeafAsset, ParentAsset]
    trg: Union[LeafAsset, ParentAsset]
    source_code: Optional[SourceCode] = None

    @model_validator(mode="after")
    def verify_allowed_relationship(self) -> "Lineage":
        if isinstance(self.src, ParentAsset) and isinstance(self.trg, LeafAsset):
            raise ValueError("If src is a ParentAsset, trg has to be a ParentAsset as well (table level lineage).")
        return self


class CustomLineageConfig:
    def __init__(self, application_name: str, output_directory: str, source_code_directory_name: str = "source_codes"):
        self.application_name = application_name
        self.output_directory_path = Path(output_directory)
        self.source_code_directory_name = source_code_directory_name

        self._create_directories()

    def _create_directories(self) -> None:
        self.source_code_directory_path.mkdir(parents=True, exist_ok=True)

    @property
    def source_code_directory_path(self) -> Path:
        return self.output_directory_path / self.source_code_directory_name
