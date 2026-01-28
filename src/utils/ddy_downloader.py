import asyncio
import re
from dataclasses import dataclass

import httpx

from src.idf.idf import IDF

GEOJSON_URL = 'https://raw.githubusercontent.com/NatLabRockies/EnergyPlus/develop/weather/master.geojson'


@dataclass
class WeatherLocation:
    province: str
    city: str
    epw: str
    ddy: str


class DDY:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def _download_geojson(self) -> dict:
        response = await self.client.get(GEOJSON_URL)
        response.raise_for_status()
        geojson = response.json()
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

    def _parse_ddy_data(self, url: str) -> IDF:
        response = httpx.get(url)
        response.raise_for_status()
        try:
            content = response.text
        except UnicodeDecodeError:
            content = response.content.decode('latin-1')
        return IDF._parse_idf_content(content)

    def get_weather_locations(self, city: str, country: str | None = 'CHN') -> IDF:
        geojson = asyncio.run(self._download_geojson())
        locations = self._parse_geojson(geojson, country)
        for location in locations:
            if location.city.lower() == city.lower():
                return self._parse_ddy_data(location.ddy or '')
        raise ValueError(f'City {city} not found in {country}')
