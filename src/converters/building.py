"""Building converter for DeST to EnergyPlus IDF conversion.

Converts Building and Environment data to:
- Building (EnergyPlus Building object - only one per IDF)
- Site:Location (latitude, longitude, time zone from coordinates)
- GlobalGeometryRules (vertex ordering rules)
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import select
from timezonefinder import TimezoneFinder

from src.converters.base import BaseConverter
from src.database.models.building import Building as DestBuilding
from src.database.models.environment import Environment
from src.idf.models.location import SiteLocation
from src.idf.models.simulation import Building as IDFBuilding
from src.idf.models.thermal_zones import GlobalGeometryRules

# Timezone finder instance (reusable for performance)
_tz_finder: TimezoneFinder | None = None


def _get_timezone_finder() -> TimezoneFinder:
    """Get or create TimezoneFinder instance."""
    global _tz_finder
    if _tz_finder is None:
        _tz_finder = TimezoneFinder()
    return _tz_finder


def get_utc_offset_from_coordinates(latitude: float, longitude: float) -> float:
    """Calculate UTC offset from geographic coordinates.

    Args:
        latitude: Latitude in degrees (-90 to 90).
        longitude: Longitude in degrees (-180 to 180).

    Returns:
        UTC offset in hours (e.g., 8.0 for UTC+8).
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tf = _get_timezone_finder()
    tz_name = tf.timezone_at(lng=longitude, lat=latitude)

    if tz_name is None:
        # Fallback: estimate from longitude (15 degrees per hour)
        logger.warning(
            f'Could not determine timezone for ({latitude}, {longitude}), '
            f'estimating from longitude'
        )
        return round(longitude / 15.0)

    # Get current UTC offset for the timezone
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    offset_seconds = now.utcoffset()
    if offset_seconds is None:
        return round(longitude / 15.0)

    return offset_seconds.total_seconds() / 3600.0


class BuildingConverter(BaseConverter[DestBuilding]):
    """Converts DeST Building and Environment to IDF objects.

    This converter creates exactly one Building object per IDF file,
    along with Site:Location and GlobalGeometryRules.

    Objects created:
    - Building: Basic building parameters (name, north axis, terrain)
    - Site:Location: Geographic location with timezone from coordinates
    - GlobalGeometryRules: Geometry rules (UpperLeftCorner, Counterclockwise)
    """

    def convert_all(self) -> None:
        """Convert Building, Environment data and add GlobalGeometryRules.

        Steps:
        1. Add GlobalGeometryRules (required for all IDF files)
        2. Add Site:Location from Environment data
        3. Create single Building object from first DeST Building
        """
        # Always add GlobalGeometryRules first
        self._add_global_geometry_rules()

        # Add Site:Location from Environment
        self._add_site_location()

        # Query buildings - we only need the first one for IDF
        stmt = select(DestBuilding)
        buildings = self.session.execute(stmt).scalars().all()
        self.stats.total = len(buildings)

        if buildings:
            # Only convert the first building (IDF supports only one)
            if self.convert_one(buildings[0]):
                self.stats.converted += 1
            else:
                self.stats.errors += 1

            if len(buildings) > 1:
                logger.warning(
                    f'Found {len(buildings)} buildings, but IDF supports only one. '
                    f'Using first building: {buildings[0].name}'
                )
                self.stats.skipped = len(buildings) - 1
        else:
            # Create default building if none exists
            self._add_default_building()

        self.log_stats()

    def convert_one(self, instance: DestBuilding) -> bool:
        """Convert a single DeST Building to IDF Building.

        Args:
            instance: DeST Building model instance.

        Returns:
            True if conversion succeeded, False otherwise.
        """
        try:
            name = self.make_name('Building', instance.building_id, instance.name)

            # Get north axis from Environment if available
            north_axis = self._get_north_axis()

            idf_building = IDFBuilding(
                name=name,
                north_axis=north_axis,
                terrain='City',  # Default terrain for urban buildings
                solar_distribution='FullExterior',
            )

            self.idf.add(idf_building)
            logger.debug(f'Converted Building: {name} (north_axis={north_axis})')
            return True

        except Exception as e:
            logger.error(f'Failed to convert Building {instance.building_id}: {e}')
            self.stats.add_warning(
                f'Building {instance.building_id} conversion failed: {e}'
            )
            return False

    def _get_north_axis(self) -> float:
        """Get north axis from Environment.south_direction.

        EnergyPlus north_axis is degrees from true North (clockwise).
        DeST south_direction is the building's south orientation angle.

        Returns:
            North axis angle in degrees.
        """
        try:
            stmt = select(Environment)
            env = self.session.execute(stmt).scalars().first()
            if env and env.south_direction is not None:
                # Convert south direction to north axis
                # south_direction = 0 means building faces true South
                return env.south_direction
        except Exception as e:
            logger.warning(f'Could not get north axis from Environment: {e}')
        return 0.0

    def _add_global_geometry_rules(self) -> None:
        """Add GlobalGeometryRules to IDF.

        EnergyPlus requires consistent geometry rules for all surfaces.
        Per plan.md: UpperLeftCorner + Counterclockwise (from outside view).
        """
        try:
            rules = GlobalGeometryRules(
                starting_vertex_position='UpperLeftCorner',
                vertex_entry_direction='Counterclockwise',
                coordinate_system='World',
                daylighting_reference_point_coordinate_system='Relative',
                rectangular_surface_coordinate_system='Relative',
            )
            self.idf.add(rules)
            logger.info(
                'Added GlobalGeometryRules: UpperLeftCorner, Counterclockwise, World'
            )
        except Exception as e:
            logger.error(f'Failed to add GlobalGeometryRules: {e}')
            self.stats.add_warning(f'GlobalGeometryRules creation failed: {e}')

    def _add_site_location(self) -> None:
        """Add Site:Location from Environment data.

        Queries Environment table for latitude, longitude, elevation,
        and calculates timezone from coordinates using timezonefinder.
        """
        try:
            stmt = select(Environment)
            env = self.session.execute(stmt).scalars().first()

            if env is None:
                logger.warning('No Environment data found, using default Site:Location')
                self._add_default_site_location()
                return

            # Use city name or environment name for location name
            location_name = env.city_name or env.name or 'Site Location'

            # Get coordinates with defaults
            latitude = env.latitude if env.latitude is not None else 39.9
            longitude = env.longitude if env.longitude is not None else 116.4
            elevation = env.elevation if env.elevation is not None else 50.0

            # Calculate time zone from coordinates
            time_zone = get_utc_offset_from_coordinates(latitude, longitude)

            location = SiteLocation(
                name=location_name,
                latitude=latitude,
                longitude=longitude,
                time_zone=time_zone,
                elevation=elevation,
            )

            self.idf.add(location)
            logger.info(
                f'Added Site:Location: {location_name} '
                f'(lat={latitude:.4f}, lon={longitude:.4f}, tz=UTC{time_zone:+.1f})'
            )

        except Exception as e:
            logger.error(f'Failed to add Site:Location: {e}')
            self.stats.add_warning(f'Site:Location creation failed: {e}')
            self._add_default_site_location()

    def _add_default_site_location(self) -> None:
        """Add default Site:Location (Beijing, China)."""
        location = SiteLocation(
            name='Default Location',
            latitude=39.9,
            longitude=116.4,
            time_zone=8.0,  # UTC+8 for Beijing
            elevation=50.0,
        )
        self.idf.add(location)
        logger.info('Added default Site:Location: Beijing (39.9, 116.4, UTC+8)')

    def _add_default_building(self) -> None:
        """Add default Building when no DeST building exists."""
        try:
            building = IDFBuilding(
                name='Default Building',
                north_axis=0.0,
                terrain='City',
                solar_distribution='FullExterior',
            )
            self.idf.add(building)
            self.stats.converted += 1
            logger.info('Added default Building object')
        except Exception as e:
            logger.error(f'Failed to add default Building: {e}')
            self.stats.errors += 1
