import re
from dataclasses import dataclass
from pathlib import Path
import json
import httpx

from src.config import PathConfig
from src.idf.idf import IDF
from src.utils.log import logger

GEOJSON_URL = 'https://raw.githubusercontent.com/NatLabRockies/EnergyPlus/develop/weather/master.geojson'
path_config = PathConfig()

@dataclass
class WeatherLocation:
    province: str
    city: str
    epw: str
    ddy: str

class DDY:
    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(timeout=timeout)
        self._timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self) -> None:
        await self.client.aclose()

    async def _download_geojson(self) -> dict:
        cache_path = path_config.output_dir / 'geojson.json'
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            response = await self.client.get(GEOJSON_URL)
            response.raise_for_status()
            geojson = response.json()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=4)
            return geojson

    def _parse_geojson(
        self, geojson: dict, country: str | None = 'CHN'
    ) -> list[WeatherLocation]:
        features = geojson['features']
        locations = []
        for feature in features:
            properties = feature['properties']
            if country and country not in properties['title']:
                continue
            province, city = self._parse_city(properties['title'])
            if not province or not city:
                continue
            epw = self._parse_epw(properties['epw'])
            ddy = self._parse_ddy(properties['ddy'])
            locations.append(WeatherLocation(province, city, epw, ddy))
        return locations

    def _parse_city(self, city: str) -> tuple[str, str]:
        match = re.match(r'[A-Z]+_([a-zA-Z]+(?:\.[a-zA-Z]+)+).\d+_CSWD', city)
        if match:
            part = match.group(1).split('.')
            return part[0], part[-1]
        return '', ''

    def _parse_epw(self, url: str) -> str:
        match = re.match(r'<a href=(.*)>Download Weather File</a>', url)
        if match:
            return match.group(1)
        return ''

    def _parse_ddy(self, url: str) -> str:
        match = re.match(r'<a href=(.*)>Download Design Day File</a>', url)
        if match:
            return match.group(1)
        return ''

    async def _parse_ddy_data(
        self, city: str, url: str, country: str | None = 'CHN'
    ) -> IDF:
        path = path_config.ddy_dir / f'{country}_{city}.ddy'
        if path.exists():
            return IDF.load(path)
        else:
            response = await self.client.get(url)
            response.raise_for_status()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return IDF.load(path)

    async def download_epw_data(
        self, city: str, url: str, country: str | None = 'CHN'
    ) -> None:
        path = path_config.weather_dir / f'{country}_{city}.epw'
        if not path.exists():
            response = await self.client.get(url)
            response.raise_for_status()
            path.write_bytes(response.content)

    async def get_weather_locations(
        self, city: str, country: str | None = 'CHN'
    ) -> IDF:
        geojson = await self._download_geojson()
        locations = self._parse_geojson(geojson, country)
        for location in locations:
            if location.city.lower() == city.lower():
                try:
                    await self.download_epw_data(location.city, location.epw, country)
                except httpx.HTTPError as e:
                    logger.error(
                        f'Failed to download EPW data for {location.city}: {e}'
                    )
                return await self._parse_ddy_data(location.city, location.ddy, country)
        raise ValueError(f'City {city} not found in {country}')
