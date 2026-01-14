"""Base class for all EnergyPlus IDF object models."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class IDFBaseModel(BaseModel):
    """Base class for all IDF object models.

    Provides common configuration and utility methods for IDF objects.

    Attributes:
        _idf_object_type: Class variable storing the original EnergyPlus object
            type name (e.g., "BuildingSurface:Detailed"). Override in subclasses.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra='forbid',
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    _idf_object_type: ClassVar[str] = ''

    @classmethod
    def idf_object_type(cls) -> str:
        """Get the EnergyPlus IDF object type name.

        Returns:
            Original object type name (e.g., "Zone", "BuildingSurface:Detailed").
        """
        return cls._idf_object_type

    def to_idf_dict(self) -> dict[str, Any]:
        """Convert model to IDF-compatible dictionary.

        Exports all non-None fields with their original names.

        Returns:
            Dictionary suitable for IDF/epJSON serialization.
        """
        return self.model_dump(exclude_none=True, by_alias=True)
