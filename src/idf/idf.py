"""Unified IDF class for EnergyPlus file handling.

This module provides the IDF class that integrates object container
and IDF file read/write functionality.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from src.idf.models import FIELD_ORDER_REGISTRY, OBJECT_TYPE_REGISTRY, get_model_class
from src.idf.models.simulation import Version

if TYPE_CHECKING:
    from src.idf.models._base import IDFBaseModel


class IDF:
    """EnergyPlus IDF file unified interface.

    Integrates object container and IDF file read/write functionality.
    Reference validation is handled automatically by RefValidator in Pydantic models.

    Attributes:
        _objects: Internal storage mapping object_type -> {name -> object}
    """

    def __init__(self) -> None:
        """Initialize empty IDF container."""
        self._objects: dict[str, dict[str, IDFBaseModel]] = {}

    @property
    def version(self) -> str:
        """Get EnergyPlus schema version from Version model default.

        Returns:
            Schema version string (e.g., '25.1').
        """
        default_version = Version()
        return default_version.version_identifier or 'Unknown'

    def add(self, obj: IDFBaseModel) -> None:
        """Add an IDF object to the container.

        Args:
            obj: IDF object instance to add.

        Raises:
            ValueError: If object with same type and name already exists.
        """
        object_type = obj.idf_object_type()
        name = getattr(obj, 'name', None) or ''

        if object_type not in self._objects:
            self._objects[object_type] = {}

        if name in self._objects[object_type]:
            raise ValueError(f"Duplicate object: {object_type} '{name}' already exists")

        self._objects[object_type][name] = obj
        logger.debug(f'Added {object_type}: {name}')

    def get(self, object_type: str, name: str) -> IDFBaseModel | None:
        """Get an object by type and name.

        Args:
            object_type: EnergyPlus object type (e.g., 'Zone').
            name: Object name.

        Returns:
            IDF object or None if not found.
        """
        return self._objects.get(object_type, {}).get(name)

    def has(self, object_type: str, name: str) -> bool:
        """Check if an object exists.

        Args:
            object_type: EnergyPlus object type.
            name: Object name.

        Returns:
            True if object exists, False otherwise.
        """
        return name in self._objects.get(object_type, {})

    def all_of_type(self, object_type: str) -> dict[str, IDFBaseModel]:
        """Get all objects of a specific type.

        Args:
            object_type: EnergyPlus object type.

        Returns:
            Dictionary mapping name to object, empty dict if type not found.
        """
        return self._objects.get(object_type, {}).copy()

    def __iter__(self) -> Iterator[IDFBaseModel]:
        """Iterate over all objects in the container.

        Yields:
            IDF objects in insertion order by type.
        """
        for objects_by_name in self._objects.values():
            yield from objects_by_name.values()

    def __len__(self) -> int:
        """Return total number of objects.

        Returns:
            Total object count across all types.
        """
        return sum(len(objects) for objects in self._objects.values())

    @classmethod
    def load(cls, path: Path) -> IDF:
        """Load IDF file and parse into object container.

        Args:
            path: Path to IDF file.

        Returns:
            IDF instance with parsed objects.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If parsing fails for any object.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'IDF file not found: {path}')

        content = path.read_text(encoding='utf-8')
        return cls._parse_idf_content(content)

    @classmethod
    def _parse_idf_content(cls, content: str) -> IDF:
        """Parse IDF content string into objects.

        Args:
            content: IDF file content.

        Returns:
            IDF instance with parsed objects.
        """
        idf = cls()

        lines = []
        for line in content.splitlines():
            if '!' in line:
                line = line.split('!')[0]
            lines.append(line)

        full_content = '\n'.join(lines)
        object_blocks = re.split(r';', full_content)

        for block in object_blocks:
            block = block.strip()
            if not block:
                continue

            fields = [f.strip() for f in block.split(',')]
            if not fields:
                continue

            object_type = fields[0]
            field_values = fields[1:]

            if object_type not in OBJECT_TYPE_REGISTRY:
                logger.warning(f'Unknown object type: {object_type}')
                continue

            model_class = get_model_class(object_type)
            if model_class is None:
                logger.warning(f'No model class for: {object_type}')
                continue

            field_order = FIELD_ORDER_REGISTRY.get(object_type, [])

            field_dict: dict[str, str | float | None] = {}
            for i, value in enumerate(field_values):
                if i >= len(field_order):
                    break
                field_name = field_order[i]
                if value:
                    field_dict[field_name] = cls._parse_field_value(value)

            try:
                obj = model_class(**field_dict)
                idf.add(obj)
            except Exception as e:
                logger.warning(f'Failed to parse {object_type}: {e}')

        return idf

    @staticmethod
    def _parse_field_value(value: str) -> str | float | None:
        """Parse a field value from IDF string.

        Args:
            value: Raw string value from IDF.

        Returns:
            Parsed value (float or string). Yes/No are kept as strings
            since many EnergyPlus fields expect string literals.
        """
        value = value.strip()
        if not value:
            return None

        try:
            return float(value)
        except ValueError:
            return value

    def save(self, path: Path) -> None:
        """Save IDF container to file.

        Uses FIELD_ORDER_REGISTRY to ensure correct field ordering.
        Float values are formatted with 6 significant digits.

        Args:
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: list[str] = []

        lines.append(f'!- Generated by destep, EnergyPlus Version {self.version}')
        lines.append('')

        for object_type in sorted(self._objects.keys()):
            objects = self._objects[object_type]
            if not objects:
                continue

            lines.append(f'!- =========== {object_type} ===========')
            lines.append('')

            field_order = FIELD_ORDER_REGISTRY.get(object_type, [])

            for obj in objects.values():
                obj_lines = self._format_object(obj, object_type, field_order)
                lines.extend(obj_lines)
                lines.append('')

        path.write_text('\n'.join(lines), encoding='utf-8')
        logger.info(f'Saved IDF with {len(self)} objects to {path}')

    def _format_object(
        self,
        obj: IDFBaseModel,
        object_type: str,
        field_order: list[str],
    ) -> list[str]:
        """Format a single object for IDF output.

        IDF format requires positional fields, so we must output all fields
        up to the last non-empty field (including empty intermediate fields).

        Handles extensible fields like 'vertices' by expanding each item's
        coordinates into separate lines.

        Args:
            obj: IDF object to format.
            object_type: Object type name.
            field_order: Ordered list of field names.

        Returns:
            List of formatted lines for the object.
        """
        lines: list[str] = []
        obj_dict = obj.model_dump(by_alias=True)

        # Separate regular fields and extensible fields (like vertices)
        regular_fields: list[tuple[str, str]] = []
        extensible_items: list[dict] = []

        for field_name in field_order:
            value = obj_dict.get(field_name)
            # Check if this is an extensible field (list of vertex items)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                extensible_items = value
            else:
                formatted = self._format_value(value)
                regular_fields.append((field_name, formatted))

        # Find last non-empty regular field
        last_non_empty_idx = -1
        for i, (_, value) in enumerate(regular_fields):
            if value:
                last_non_empty_idx = i

        # Handle case with no regular fields
        if last_non_empty_idx < 0 and not extensible_items:
            lines.append(f'{object_type};')
            return lines

        # Build output
        lines.append(f'{object_type},')

        # Output regular fields (up to last non-empty or all if we have extensible)
        if extensible_items:
            # Include all regular fields when we have extensible items
            fields_to_output = regular_fields
        else:
            fields_to_output = regular_fields[: last_non_empty_idx + 1]

        for i, (field_name, value) in enumerate(fields_to_output):
            is_last = i == len(fields_to_output) - 1 and not extensible_items
            terminator = ';' if is_last else ','
            comment = f'!- {field_name}'
            lines.append(f'    {value}{terminator}  {comment}')

        # Output extensible items (vertices)
        if extensible_items:
            for idx, item in enumerate(extensible_items):
                is_last_item = idx == len(extensible_items) - 1
                vertex_line = self._format_vertex_item(item, idx + 1, is_last_item)
                lines.append(vertex_line)

        return lines

    def _format_vertex_item(self, item: dict, vertex_num: int, is_last: bool) -> str:
        """Format a single vertex item for IDF output.

        Args:
            item: Dictionary with vertex_x_coordinate, vertex_y_coordinate,
                  vertex_z_coordinate keys.
            vertex_num: 1-based vertex number for comment.
            is_last: Whether this is the last vertex.

        Returns:
            Formatted vertex line.
        """
        x = item.get('vertex_x_coordinate', 0)
        y = item.get('vertex_y_coordinate', 0)
        z = item.get('vertex_z_coordinate', 0)

        x_str = f'{x:.6g}' if isinstance(x, float) else str(x)
        y_str = f'{y:.6g}' if isinstance(y, float) else str(y)
        z_str = f'{z:.6g}' if isinstance(z, float) else str(z)

        terminator = ';' if is_last else ','
        comment = f'!- X,Y,Z ==> Vertex {vertex_num} {{m}}'

        return f'    {x_str}, {y_str}, {z_str}{terminator}  {comment}'

    @staticmethod
    def _format_value(value: object) -> str:
        """Format a value for IDF output.

        Args:
            value: Value to format.

        Returns:
            Formatted string value.
        """
        if value is None:
            return ''
        if isinstance(value, bool):
            return 'Yes' if value else 'No'
        if isinstance(value, float):
            return f'{value:.6g}'
        return str(value)
