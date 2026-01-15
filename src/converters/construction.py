"""Construction converter for DeST to EnergyPlus IDF conversion.

Converts DeST construction data (walls, floors, roofs) to:
- Material: Thermal properties of individual materials
- Construction: Layer assemblies with materials from outside to inside

Only constructions referenced by MainEnclosure are converted.

DeST construction types (MainEnclosure.kind):
- 1: 外墙 (SysOutwall)
- 2: 内墙 (SysInwall)
- 3: 屋顶 (SysRoof)
- 4: 楼地 (SysGroundfloor)
- 5: 地板/天花板 (SysMiddlefloor)
- 6: 挑空楼板 (SysAirfloor)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.converters.base import BaseConverter, UnitConverter
from src.database.models.construction import (
    MainEnclosure,
    SysAirfloor,
    SysAirfloorMaterial,
    SysGroundfloor,
    SysGroundfloorMaterial,
    SysInwall,
    SysInwallMaterial,
    SysMaterial,
    SysMiddlefloor,
    SysMiddlefloorMaterial,
    SysOutwall,
    SysOutwallMaterial,
    SysRoof,
    SysRoofMaterial,
)
from src.idf import IDF
from src.idf.models.constructions import Construction, Material
from src.utils.pinyin import PinyinConverter

if TYPE_CHECKING:
    pass


class ConstructionKind(IntEnum):
    """DeST construction kind enumeration (MainEnclosure.kind).

    These map to different sys_* tables in the DeST database.
    """

    OUTWALL = 1  # 外墙
    INWALL = 2  # 内墙
    ROOF = 3  # 屋顶
    GROUNDFLOOR = 4  # 楼地
    MIDDLEFLOOR = 5  # 地板/天花板
    AIRFLOOR = 6  # 挑空楼板


# Mapping from construction kind to IDF construction name prefix
CONSTRUCTION_KIND_PREFIX: dict[int, str] = {
    ConstructionKind.OUTWALL: 'ExtWall',
    ConstructionKind.INWALL: 'IntWall',
    ConstructionKind.ROOF: 'Roof',
    ConstructionKind.GROUNDFLOOR: 'GroundFloor',
    ConstructionKind.MIDDLEFLOOR: 'IntFloor',
    ConstructionKind.AIRFLOOR: 'AirFloor',
}


@dataclass
class DefaultMaterialProps:
    """Default material properties for when data is missing."""

    conductivity: float = 1.0  # W/m-K
    density: float = 2000.0  # kg/m³
    specific_heat: float = 1000.0  # J/kg-K
    thickness: float = 0.1  # m


# Default material properties
DEFAULT_MATERIAL = DefaultMaterialProps()


class ConstructionConverter(BaseConverter[MainEnclosure]):
    """Converts DeST constructions to IDF Material and Construction objects.

    Only constructions referenced by MainEnclosure are converted.
    Each DeST construction is converted to:
    1. Multiple Material objects (one per layer)
    2. One Construction object that references the materials

    Note: Material layers are ordered from outside to inside per EnergyPlus.
    DeST stores layers with layer_no starting from 1 (outside).
    """

    def __init__(
        self,
        session: Session,
        idf: IDF,
        pinyin: PinyinConverter | None = None,
    ) -> None:
        """Initialize ConstructionConverter.

        Args:
            session: SQLAlchemy database session.
            idf: IDF instance to add converted objects to.
            pinyin: PinyinConverter for Chinese name conversion.
        """
        super().__init__(session, idf, pinyin)
        self._created_constructions: dict[
            tuple[int, int], str
        ] = {}  # (kind, id) -> name
        self._default_material_counter: int = 0

    def convert_all(self) -> None:
        """Convert all referenced constructions from MainEnclosure.

        Steps:
        1. Query MainEnclosure to find all referenced (kind, construction) pairs
        2. Convert only those constructions that are actually used
        """
        # Get all unique (kind, construction) pairs from MainEnclosure
        stmt = select(MainEnclosure.kind, MainEnclosure.construction).distinct()
        result = self.session.execute(stmt).all()

        # Filter out invalid entries
        referenced: set[tuple[int, int]] = set()
        for kind, construction_id in result:
            if kind is not None and construction_id is not None:
                referenced.add((kind, construction_id))

        self.stats.total = len(referenced)
        logger.info(
            f'Found {len(referenced)} unique constructions referenced by MainEnclosure'
        )

        # Convert each referenced construction
        for kind, construction_id in referenced:
            if self._convert_construction(kind, construction_id):
                self.stats.converted += 1
            else:
                self.stats.errors += 1

        self.log_stats()

    def convert_one(self, instance: MainEnclosure) -> bool:
        """Convert the construction referenced by a MainEnclosure.

        Args:
            instance: MainEnclosure instance.

        Returns:
            True if conversion succeeded.
        """
        if instance.kind is None or instance.construction is None:
            return False
        return self._convert_construction(instance.kind, instance.construction)

    def get_construction_name(
        self,
        kind: int,
        construction_id: int,
    ) -> str | None:
        """Get the IDF construction name for a given DeST construction.

        Use this after conversion to get construction names for surface references.

        Args:
            kind: ConstructionKind enum value (MainEnclosure.kind).
            construction_id: Construction ID (MainEnclosure.construction).

        Returns:
            IDF construction name if converted, None otherwise.
        """
        return self._created_constructions.get((kind, construction_id))

    def _convert_construction(self, kind: int, construction_id: int) -> bool:
        """Convert a single construction by kind and ID.

        Args:
            kind: Construction kind (1-6).
            construction_id: Structure ID in the corresponding sys_* table.

        Returns:
            True if conversion succeeded.
        """
        # Check if already converted
        if (kind, construction_id) in self._created_constructions:
            return True

        # Route to type-specific conversion methods
        if kind == ConstructionKind.OUTWALL:
            return self._convert_outwall(construction_id)
        elif kind == ConstructionKind.INWALL:
            return self._convert_inwall(construction_id)
        elif kind == ConstructionKind.ROOF:
            return self._convert_roof(construction_id)
        elif kind == ConstructionKind.GROUNDFLOOR:
            return self._convert_groundfloor(construction_id)
        elif kind == ConstructionKind.MIDDLEFLOOR:
            return self._convert_middlefloor(construction_id)
        elif kind == ConstructionKind.AIRFLOOR:
            return self._convert_airfloor(construction_id)
        else:
            logger.warning(f'Unknown construction kind {kind}, skipping')
            self.stats.skipped += 1
            return False

    def _convert_outwall(self, construction_id: int) -> bool:
        """Convert an exterior wall construction."""
        stmt = select(SysOutwall).where(SysOutwall.struct_id == construction_id)
        construction = self.session.execute(stmt).scalars().first()
        if construction is None:
            logger.warning(f'Outwall {construction_id} not found')
            self.stats.skipped += 1
            return False

        stmt = (
            select(SysOutwallMaterial)
            .where(SysOutwallMaterial.struct_id == construction_id)
            .order_by(SysOutwallMaterial.layer_no)
        )
        layers = list(self.session.execute(stmt).scalars().all())
        if not layers:
            logger.warning(f'Outwall {construction_id} has no layers')
            self.stats.skipped += 1
            return False

        return self._create_construction(
            ConstructionKind.OUTWALL,
            construction_id,
            construction.cname or construction.name,
            layers,
        )

    def _convert_inwall(self, construction_id: int) -> bool:
        """Convert an interior wall construction."""
        stmt = select(SysInwall).where(SysInwall.struct_id == construction_id)
        construction = self.session.execute(stmt).scalars().first()
        if construction is None:
            logger.warning(f'Inwall {construction_id} not found')
            self.stats.skipped += 1
            return False

        stmt = (
            select(SysInwallMaterial)
            .where(SysInwallMaterial.struct_id == construction_id)
            .order_by(SysInwallMaterial.layer_no)
        )
        layers = list(self.session.execute(stmt).scalars().all())
        if not layers:
            logger.warning(f'Inwall {construction_id} has no layers')
            self.stats.skipped += 1
            return False

        return self._create_construction(
            ConstructionKind.INWALL,
            construction_id,
            construction.cname or construction.name,
            layers,
        )

    def _convert_roof(self, construction_id: int) -> bool:
        """Convert a roof construction."""
        stmt = select(SysRoof).where(SysRoof.struct_id == construction_id)
        construction = self.session.execute(stmt).scalars().first()
        if construction is None:
            logger.warning(f'Roof {construction_id} not found')
            self.stats.skipped += 1
            return False

        stmt = (
            select(SysRoofMaterial)
            .where(SysRoofMaterial.struct_id == construction_id)
            .order_by(SysRoofMaterial.layer_no)
        )
        layers = list(self.session.execute(stmt).scalars().all())
        if not layers:
            logger.warning(f'Roof {construction_id} has no layers')
            self.stats.skipped += 1
            return False

        return self._create_construction(
            ConstructionKind.ROOF,
            construction_id,
            construction.cname or construction.name,
            layers,
        )

    def _convert_groundfloor(self, construction_id: int) -> bool:
        """Convert a ground floor construction."""
        stmt = select(SysGroundfloor).where(SysGroundfloor.struct_id == construction_id)
        construction = self.session.execute(stmt).scalars().first()
        if construction is None:
            logger.warning(f'Groundfloor {construction_id} not found')
            self.stats.skipped += 1
            return False

        stmt = (
            select(SysGroundfloorMaterial)
            .where(SysGroundfloorMaterial.struct_id == construction_id)
            .order_by(SysGroundfloorMaterial.layer_no)
        )
        layers = list(self.session.execute(stmt).scalars().all())
        if not layers:
            logger.warning(f'Groundfloor {construction_id} has no layers')
            self.stats.skipped += 1
            return False

        return self._create_construction(
            ConstructionKind.GROUNDFLOOR,
            construction_id,
            construction.cname or construction.name,
            layers,
        )

    def _convert_middlefloor(self, construction_id: int) -> bool:
        """Convert a middle floor construction."""
        stmt = select(SysMiddlefloor).where(SysMiddlefloor.struct_id == construction_id)
        construction = self.session.execute(stmt).scalars().first()
        if construction is None:
            logger.warning(f'Middlefloor {construction_id} not found')
            self.stats.skipped += 1
            return False

        stmt = (
            select(SysMiddlefloorMaterial)
            .where(SysMiddlefloorMaterial.struct_id == construction_id)
            .order_by(SysMiddlefloorMaterial.layer_no)
        )
        layers = list(self.session.execute(stmt).scalars().all())
        if not layers:
            logger.warning(f'Middlefloor {construction_id} has no layers')
            self.stats.skipped += 1
            return False

        return self._create_construction(
            ConstructionKind.MIDDLEFLOOR,
            construction_id,
            construction.cname or construction.name,
            layers,
        )

    def _convert_airfloor(self, construction_id: int) -> bool:
        """Convert an air floor construction."""
        stmt = select(SysAirfloor).where(SysAirfloor.struct_id == construction_id)
        construction = self.session.execute(stmt).scalars().first()
        if construction is None:
            logger.warning(f'Airfloor {construction_id} not found')
            self.stats.skipped += 1
            return False

        stmt = (
            select(SysAirfloorMaterial)
            .where(SysAirfloorMaterial.struct_id == construction_id)
            .order_by(SysAirfloorMaterial.layer_no)
        )
        layers = list(self.session.execute(stmt).scalars().all())
        if not layers:
            logger.warning(f'Airfloor {construction_id} has no layers')
            self.stats.skipped += 1
            return False

        return self._create_construction(
            ConstructionKind.AIRFLOOR,
            construction_id,
            construction.cname or construction.name,
            layers,
        )

    def _create_construction(
        self,
        kind: int,
        construction_id: int,
        name: str | None,
        layers: list[Any],
    ) -> bool:
        """Create IDF Construction and Material objects.

        Args:
            kind: Construction kind (1-6).
            construction_id: Structure ID from DeST database.
            name: Construction name (Chinese or English).
            layers: List of material layer model instances.

        Returns:
            True if construction was created successfully.
        """
        prefix = CONSTRUCTION_KIND_PREFIX.get(kind, 'Construction')
        construction_name = self.make_name(prefix, construction_id, name)

        # Create materials and collect names
        material_names: list[str] = []
        for layer in layers:
            material_name = self._get_or_create_material(
                layer,
                construction_name,
                layer.layer_no,
            )
            if material_name:
                material_names.append(material_name)

        if not material_names:
            self.stats.add_warning(
                f'Construction {construction_name} has no valid materials, skipping'
            )
            return False

        # EnergyPlus supports up to 10 layers
        if len(material_names) > 10:
            logger.warning(
                f'Construction {construction_name} has {len(material_names)} layers, '
                f'truncating to 10'
            )
            material_names = material_names[:10]

        # Create Construction object
        try:
            # Build layer arguments (layer_2 through layer_10 are optional)
            layer_kwargs: dict[str, str] = {'outside_layer': material_names[0]}
            for i, mat_name in enumerate(material_names[1:], start=2):
                layer_kwargs[f'layer_{i}'] = mat_name

            construction = Construction(name=construction_name, **layer_kwargs)
            self.idf.add(construction)

            # Record the mapping
            self._created_constructions[(kind, construction_id)] = construction_name

            logger.debug(
                f'Created Construction: {construction_name} '
                f'with {len(material_names)} layers'
            )
            return True

        except Exception as e:
            logger.error(f'Failed to create Construction {construction_name}: {e}')
            self.stats.add_warning(f'Construction {construction_name} failed: {e}')
            return False

    def _get_or_create_material(
        self,
        layer: Any,
        construction_name: str,
        layer_no: int,
    ) -> str | None:
        """Get or create an IDF Material for a layer.

        Args:
            layer: Material layer model instance (e.g., SysOutwallMaterial).
            construction_name: Parent construction name for unique naming.
            layer_no: Layer number for naming.

        Returns:
            Material name if successful, None otherwise.
        """
        material_id = layer.material_id
        thickness_mm = layer.length  # DeST stores thickness as 'length' in mm

        # Handle missing material reference
        if material_id is None:
            return self._create_default_material(
                construction_name, layer_no, thickness_mm
            )

        # Query the material properties
        stmt = select(SysMaterial).where(SysMaterial.material_id == material_id)
        material = self.session.execute(stmt).scalars().first()

        if material is None:
            logger.warning(
                f'Material ID {material_id} not found for {construction_name} layer {layer_no}'
            )
            return self._create_default_material(
                construction_name, layer_no, thickness_mm
            )

        return self._create_material(
            material, construction_name, layer_no, thickness_mm
        )

    def _create_material(
        self,
        material: SysMaterial,
        construction_name: str,
        layer_no: int,
        thickness_mm: float | None,
    ) -> str | None:
        """Create an IDF Material object.

        Args:
            material: SysMaterial model instance.
            construction_name: Parent construction name.
            layer_no: Layer number.
            thickness_mm: Layer thickness in millimeters.

        Returns:
            Material name if successful, None otherwise.
        """
        try:
            # Generate unique name combining material info and layer position
            base_name = (
                material.cname or material.name or f'Material_{material.material_id}'
            )
            material_name = (
                f'{construction_name}_L{layer_no}_{self.pinyin.convert(base_name)}'
            )

            # Convert thickness from mm to m
            thickness_m = UnitConverter.mm_to_m(thickness_mm)
            if thickness_m <= 0:
                thickness_m = 0.01  # Minimum 1cm default

            # Get thermal properties with defaults
            conductivity = material.conductivity
            density = material.density
            specific_heat = material.specific_heat

            # Validate and apply defaults for missing properties
            if conductivity is None or conductivity <= 0:
                conductivity = DEFAULT_MATERIAL.conductivity
                logger.debug(
                    f'Material {material_name}: using default conductivity {conductivity}'
                )

            if density is None or density <= 0:
                density = DEFAULT_MATERIAL.density
                logger.debug(
                    f'Material {material_name}: using default density {density}'
                )

            if specific_heat is None or specific_heat < 100:
                specific_heat = DEFAULT_MATERIAL.specific_heat
                logger.debug(
                    f'Material {material_name}: using default specific_heat {specific_heat}'
                )

            # Create Material object
            idf_material = Material(
                name=material_name,
                roughness='MediumRough',
                thickness=round(thickness_m, 4),
                conductivity=round(conductivity, 4),
                density=round(density, 2),
                specific_heat=round(specific_heat, 2),
            )

            self.idf.add(idf_material)
            logger.debug(
                f'Created Material: {material_name} '
                f'(t={thickness_m:.4f}m, k={conductivity:.4f}W/m-K)'
            )
            return material_name

        except Exception as e:
            logger.error(f'Failed to create material for layer {layer_no}: {e}')
            return self._create_default_material(
                construction_name, layer_no, thickness_mm
            )

    def _create_default_material(
        self,
        construction_name: str,
        layer_no: int,
        thickness_mm: float | None,
    ) -> str | None:
        """Create a default material when data is missing.

        Args:
            construction_name: Parent construction name.
            layer_no: Layer number.
            thickness_mm: Layer thickness in millimeters (may be None).

        Returns:
            Material name if successful, None otherwise.
        """
        try:
            self._default_material_counter += 1
            material_name = f'{construction_name}_L{layer_no}_Default{self._default_material_counter}'

            # Convert thickness
            thickness_m = UnitConverter.mm_to_m(thickness_mm)
            if thickness_m <= 0:
                thickness_m = DEFAULT_MATERIAL.thickness

            idf_material = Material(
                name=material_name,
                roughness='MediumRough',
                thickness=round(thickness_m, 4),
                conductivity=DEFAULT_MATERIAL.conductivity,
                density=DEFAULT_MATERIAL.density,
                specific_heat=DEFAULT_MATERIAL.specific_heat,
            )

            self.idf.add(idf_material)
            logger.warning(
                f'Created default Material: {material_name} '
                f'(t={thickness_m:.4f}m) for missing material data'
            )
            return material_name

        except Exception as e:
            logger.error(f'Failed to create default material: {e}')
            self.stats.add_warning(f'Default material creation failed: {e}')
            return None
