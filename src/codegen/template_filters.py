"""Jinja2 template filters for IDF model code generation.

This module provides filter functions used by idf_model_py.jinja2 template.
These filters are registered with the Jinja2 environment by ModelGenerator.
"""

from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING, Any

from .field_parser import _UNSET, FieldSpec

if TYPE_CHECKING:
    from .schema_parser import ObjectSpec


def python_type_filter(spec: FieldSpec) -> str:
    """Convert FieldSpec to Python type annotation string.

    This filter generates the complete type annotation including `| None`
    suffix for optional fields.

    Args:
        spec: Field specification to convert.

    Returns:
        Python type annotation as string.

    Examples:
        - number (required) -> "float"
        - number (optional) -> "float | None"
        - string with enum -> 'Literal["A", "B"]'
        - array of numbers -> "list[float]"
        - array of objects -> "list[VertexItem]" (nested class name)
    """
    base_type = _get_base_type_annotation(spec)
    is_opt = is_optional_filter(spec)

    if is_opt and '| None' not in base_type:
        return f'{base_type} | None'
    return base_type


def _get_base_type_annotation(spec: FieldSpec) -> str:
    """Get base type annotation without optional suffix.

    Args:
        spec: Field specification.

    Returns:
        Base type annotation string.
    """
    if spec.enum_values:
        escaped = [repr(v) for v in spec.enum_values]
        return f'Literal[{", ".join(escaped)}]'

    if spec.anyof_specs:
        has_null = any(s.field_type == 'null' for s in spec.anyof_specs)
        non_null_types = [s for s in spec.anyof_specs if s.field_type != 'null']

        if len(non_null_types) == 1:
            base = _json_type_to_python(non_null_types[0].field_type)
            if non_null_types[0].enum_values:
                escaped = [repr(v) for v in non_null_types[0].enum_values]
                base = f'Literal[{", ".join(escaped)}]'
            return f'{base} | None' if has_null else base

        types = []
        for s in non_null_types:
            if s.enum_values:
                escaped = [repr(v) for v in s.enum_values]
                types.append(f'Literal[{", ".join(escaped)}]')
            else:
                types.append(_json_type_to_python(s.field_type))

        type_str = ' | '.join(types)
        return f'{type_str} | None' if has_null else type_str

    if spec.field_type == 'array':
        if spec.items_spec:
            if spec.items_spec.nested_fields:
                # Check for pre-computed class name (set by extract_nested_classes)
                # Falls back to generating from field name
                item_class = getattr(
                    spec.items_spec,
                    'item_class_name',
                    _generate_nested_class_name(spec.name),
                )
                return f'list[{item_class}]'
            item_type = _json_type_to_python(spec.items_spec.field_type)
            return f'list[{item_type}]'
        return 'list[Any]'

    return _json_type_to_python(spec.field_type)


def _json_type_to_python(field_type: str) -> str:
    """Map JSON schema type to Python type.

    Args:
        field_type: JSON schema type string.

    Returns:
        Python type string.
    """
    type_mapping = {
        'number': 'float',
        'integer': 'int',
        'string': 'str',
        'boolean': 'bool',
        'object': 'dict[str, Any]',
        'null': 'None',
        'array': 'list[Any]',
    }
    return type_mapping.get(field_type, 'Any')


def _generate_nested_class_name(
    field_name: str, parent_class: str | None = None
) -> str:
    """Generate a class name for nested array item types.

    Args:
        field_name: Original field name (e.g., "vertices").
        parent_class: Optional parent class name for disambiguation.

    Returns:
        PascalCase class name (e.g., "VerticesItem" or "BuildingSurfaceDetailedVerticesItem").
    """
    # Convert field name to PascalCase
    parts = re.split(r'[_\s-]+', field_name)
    pascal = ''.join(p.capitalize() for p in parts if p)

    if parent_class:
        return f'{parent_class}{pascal}Item'
    return f'{pascal}Item'


def extract_nested_classes(
    objects: list[ObjectSpec],
    deduplicate: bool = True,
) -> list[dict[str, Any]]:
    """Extract nested class definitions from object specifications.

    This function scans all objects for array fields with nested object items
    and generates class definitions for them. It also sets the `item_class_name`
    attribute on the `items_spec` so that `python_type_filter` can use it.

    Args:
        objects: List of ObjectSpec instances.
        deduplicate: If True, merge structurally identical nested classes.

    Returns:
        List of nested class dicts with "name" and "fields" keys.
        Also modifies items_spec.item_class_name in-place for type generation.
    """
    nested_classes: list[dict[str, Any]] = []
    seen_structures: dict[str, str] = {}  # structure hash -> class name

    for obj in objects:
        for field in obj.fields:
            if (
                field.field_type == 'array'
                and field.items_spec
                and field.items_spec.nested_fields
            ):
                nested_fields = field.items_spec.nested_fields

                if deduplicate:
                    structure_sig = _get_structure_signature(nested_fields)
                    if structure_sig in seen_structures:
                        field.items_spec.item_class_name = seen_structures[
                            structure_sig
                        ]
                        continue

                class_name = _generate_nested_class_name(field.name, obj.class_name)

                nested_classes.append({'name': class_name, 'fields': nested_fields})

                field.items_spec.item_class_name = class_name

                if deduplicate:
                    seen_structures[structure_sig] = class_name

    return nested_classes


def _get_structure_signature(fields: list[FieldSpec]) -> str:
    """Generate a signature string representing field structure.

    Used for deduplication of structurally identical nested classes.

    Args:
        fields: List of field specifications.

    Returns:
        String signature for comparison.
    """
    if not fields:
        return '<empty>'
    parts = []
    for f in sorted(fields, key=lambda x: x.name):
        parts.append(f'{f.name}:{f.field_type}:{f.required}')
    return '|'.join(parts)


def is_optional_filter(spec: FieldSpec) -> bool:
    """Determine if a field should be optional in the Pydantic model.

    A field is optional if:
    - It has an explicit default value (including None from schema)
    - It is not in the required list
    - It has anyOf with null type

    Args:
        spec: Field specification to check.

    Returns:
        True if the field should be optional.
    """
    # Has explicit default value (including None from schema "default": null)
    if spec.default is not _UNSET:
        return True

    # Not required
    if not spec.required:
        return True

    # anyOf includes null type
    if spec.anyof_specs:
        return any(s.field_type == 'null' for s in spec.anyof_specs)

    return False


def field_definition_filter(spec: FieldSpec) -> str:
    """Generate complete Field(...) definition string.

    Args:
        spec: Field specification.

    Returns:
        Field(...) call as string.

    Examples:
        - Required field: 'Field(...)'
        - With default: 'Field(default=0.0)'
        - With constraints: 'Field(default=1, ge=1)'
        - With metadata: 'Field(default=0.0, json_schema_extra={"units": "m"})'
    """
    args: list[str] = []

    # Default value
    if _has_default(spec):
        default_repr = _format_default_value(spec.default, spec)
        args.append(f'default={default_repr}')
    elif is_optional_filter(spec):
        args.append('default=None')
    else:
        args.append('...')

    # Numeric constraints
    if spec.minimum is not None:
        args.append(f'ge={spec.minimum}')
    if spec.maximum is not None:
        args.append(f'le={spec.maximum}')
    if spec.exclusive_minimum is not None:
        args.append(f'gt={spec.exclusive_minimum}')
    if spec.exclusive_maximum is not None:
        args.append(f'lt={spec.exclusive_maximum}')

    # Metadata as json_schema_extra
    metadata = _build_metadata(spec)
    if metadata:
        args.append(f'json_schema_extra={metadata!r}')

    return f'Field({", ".join(args)})'


def _has_default(spec: FieldSpec) -> bool:
    """Check if field has an explicit default value.

    Returns True if default was explicitly set in schema (even to null/None).
    _UNSET means no default was specified in schema.

    Args:
        spec: Field specification.

    Returns:
        True if field has an explicit default (including None).
    """
    return spec.default is not _UNSET


def _format_default_value(value: Any, spec: FieldSpec | None = None) -> str:
    """Format default value for Python code.

    Args:
        value: Default value to format.
        spec: Optional field specification for type-aware formatting.

    Returns:
        Python repr string suitable for code generation.
    """
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, (int, float)):
        # Handle schema inconsistency: field_type is string but default is number
        # (e.g., Version.version_identifier has type="string" but default=25.1)
        if spec and spec.field_type == 'string':
            return repr(str(value))

        # Handle case where enum has integer values but default is float
        if spec and isinstance(value, float) and value == int(value):
            # Check direct enum_values
            if spec.enum_values:
                if all(isinstance(v, int) for v in spec.enum_values):
                    return repr(int(value))
            # Check anyof_specs for enum values (for union types)
            elif spec.anyof_specs:
                for anyof_spec in spec.anyof_specs:
                    if anyof_spec.enum_values and all(
                        isinstance(v, int) for v in anyof_spec.enum_values
                    ):
                        return repr(int(value))
        return repr(value)
    if value is None:
        return 'None'
    # For complex types, use repr
    return repr(value)


def _build_metadata(spec: FieldSpec) -> dict[str, Any]:
    """Build metadata dictionary for json_schema_extra.

    Args:
        spec: Field specification.

    Returns:
        Metadata dictionary (empty if no metadata).
    """
    metadata: dict[str, Any] = {}

    if spec.units:
        metadata['units'] = spec.units
    if spec.object_list:
        metadata['object_list'] = spec.object_list
    if spec.note:
        # Truncate long notes
        note = spec.note
        if len(note) > 200:
            note = note[:197] + '...'
        metadata['note'] = note

    return metadata


def format_docstring_filter(text: str | None, width: int = 76) -> str:
    """Format text for use as a docstring.

    Wraps long text and escapes special characters.

    Args:
        text: Raw docstring text.
        width: Maximum line width.

    Returns:
        Formatted docstring text.
    """
    if not text:
        return ''

    # Remove excessive whitespace
    text = ' '.join(text.split())

    # Escape backslashes and quotes
    text = text.replace('\\', '\\\\').replace('"', '\\"')

    # Wrap long lines
    if len(text) <= width:
        return text

    wrapped = textwrap.fill(text, width=width)
    return wrapped


# Registry of all template filters
TEMPLATE_FILTERS: dict[str, Any] = {
    'python_type': python_type_filter,
    'is_optional': is_optional_filter,
    'field_definition': field_definition_filter,
    'format_docstring': format_docstring_filter,
}
