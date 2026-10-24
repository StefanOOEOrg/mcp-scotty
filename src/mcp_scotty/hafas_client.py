"""Direct HAFAS API Client - bypassing pyhafas for better control."""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class HafasConfig:
    """Configuration for HAFAS API endpoint."""

    endpoint: str
    aid: str  # Authentication ID
    client_id: str
    client_name: str
    client_version: str
    api_version: str = "1.16"
    language: str = "de"


# Provider-specific configurations
HAFAS_CONFIGS = {
    "oebb": HafasConfig(
        endpoint="https://fahrplan.oebb.at/bin/mgate.exe",
        aid="OWDL4fE4ixNiPBBm",
        client_id="OEBB",
        client_name="oebbANDROID",
        client_version="100600",
    ),
    "db": HafasConfig(
        endpoint="https://reiseauskunft.bahn.de/bin/mgate.exe",
        aid="n91dB8Z77MLdoR0K",
        client_id="DB",
        client_name="DB Navigator",
        client_version="23040000",
    ),
    "sbb": HafasConfig(
        endpoint="https://fahrplan.sbb.ch/bin/mgate.exe",
        aid="2c4f8620337e48fb",
        client_id="SBB",
        client_name="SBBmobile",
        client_version="6.15.10.8.8",
        language="en",
    ),
    "ns": HafasConfig(
        endpoint="https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips",
        aid="",  # NS uses different auth
        client_id="NS",
        client_name="NS",
        client_version="1.0",
        language="en",
    ),
}


class HafasClient:
    """Direct HAFAS API client."""

    def __init__(self, config: HafasConfig, disable_ssl_verify: bool = False):
        """Initialize HAFAS client.

        Args:
            config: HAFAS configuration for specific provider
            disable_ssl_verify: Disable SSL verification (for testing only)
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8',
            'Accept-Encoding': 'gzip',
            'Content-Type': 'application/json',
            'User-Agent': 'mcp-scotty/0.3.0',
        })
        self.disable_ssl_verify = disable_ssl_verify

        if disable_ssl_verify:
            logger.warning("SSL verification is DISABLED - only use for testing!")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to HAFAS API.

        Args:
            method: HAFAS method name (e.g., 'LocMatch', 'TripSearch')
            params: Method-specific parameters

        Returns:
            Response dictionary
        """
        # Build request body
        request_body = {
            "auth": {
                "type": "AID",
                "aid": self.config.aid
            },
            "client": {
                "id": self.config.client_id,
                "name": self.config.client_name,
                "type": "AND",
                "v": self.config.client_version
            },
            "ver": self.config.api_version,
            "lang": self.config.language,
            "svcReqL": [
                {
                    "meth": method,
                    "req": params
                }
            ]
        }

        logger.debug(f"HAFAS request: {method} to {self.config.endpoint}")

        try:
            response = self.session.post(
                self.config.endpoint,
                json=request_body,
                verify=not self.disable_ssl_verify,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Check for errors in response
            if 'svcResL' in data and len(data['svcResL']) > 0:
                svc_res = data['svcResL'][0]
                if svc_res.get('err') != 'OK':
                    error_msg = svc_res.get('errTxt', 'Unknown error')
                    raise Exception(f"HAFAS error: {error_msg}")
                return svc_res.get('res', {})

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            logger.error(f"Response text: {response.text[:500]}")
            raise Exception("HAFAS API returned invalid JSON")

    def search_locations(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for stations/locations.

        Args:
            query: Search query (station name)
            max_results: Maximum number of results

        Returns:
            List of location dictionaries
        """
        params = {
            "input": query,  # Simple string input
            "maxNo": max_results,
            "field": "S"  # Station only
        }

        try:
            response = self._make_request("LocMatch", params)
            locations = response.get('match', {}).get('locL', [])
            return locations
        except Exception as e:
            logger.error(f"Location search failed: {e}")
            raise

    def get_journeys(
        self,
        origin_id: str,
        dest_id: str,
        date: Optional[datetime] = None,
        max_journeys: int = 5
    ) -> List[Dict[str, Any]]:
        """Get journey connections between two stations.

        Args:
            origin_id: Origin station ID
            dest_id: Destination station ID
            date: Departure date/time
            max_journeys: Maximum number of journeys

        Returns:
            List of journey dictionaries
        """
        if date is None:
            date = datetime.now()

        params = {
            "depLocL": [{"lid": origin_id}],
            "arrLocL": [{"lid": dest_id}],
            "outDate": date.strftime("%Y%m%d"),
            "outTime": date.strftime("%H%M%S"),
            "maxChg": 10,  # Max number of transfers
            "numF": max_journeys
        }

        try:
            response = self._make_request("TripSearch", params)
            journeys = response.get('outConL', [])
            return journeys
        except Exception as e:
            logger.error(f"Journey search failed: {e}")
            raise

    def get_departures(
        self,
        station_id: str,
        date: Optional[datetime] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get departures from a station.

        Args:
            station_id: Station ID
            date: Date/time for departures
            max_results: Maximum number of results

        Returns:
            List of departure dictionaries
        """
        if date is None:
            date = datetime.now()

        params = {
            "locL": [{"lid": station_id}],
            "date": date.strftime("%Y%m%d"),
            "time": date.strftime("%H%M%S"),
            "maxJny": max_results,
            "type": "DEP"  # Departures
        }

        try:
            response = self._make_request("StationBoard", params)
            departures = response.get('jnyL', [])
            return departures
        except Exception as e:
            logger.error(f"Departures request failed: {e}")
            raise

    def get_arrivals(
        self,
        station_id: str,
        date: Optional[datetime] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get arrivals at a station.

        Args:
            station_id: Station ID
            date: Date/time for arrivals
            max_results: Maximum number of results

        Returns:
            List of arrival dictionaries
        """
        if date is None:
            date = datetime.now()

        params = {
            "locL": [{"lid": station_id}],
            "date": date.strftime("%Y%m%d"),
            "time": date.strftime("%H%M%S"),
            "maxJny": max_results,
            "type": "ARR"  # Arrivals
        }

        try:
            response = self._make_request("StationBoard", params)
            arrivals = response.get('jnyL', [])
            return arrivals
        except Exception as e:
            logger.error(f"Arrivals request failed: {e}")
            raise
