"""Tests for the provider profiles (WP4).

These are characterisation tests: they pin the profile data and the lookup
behaviour so the cleanup of the remaining ruff findings cannot change it.
"""

import json

import pytest

from mcp_scotty.hafas_client import HAFAS_CONFIGS
from mcp_scotty.profiles import PROFILES, TransitProfile, get_profile, list_profiles


def test_the_four_known_providers_are_configured():
    assert list(PROFILES) == ["oebb", "db", "sbb", "ns"]


def test_every_profile_has_the_fields_a_client_needs():
    for key, profile in PROFILES.items():
        assert isinstance(profile, TransitProfile)
        assert key == profile.hafas_profile_id
        assert profile.name and profile.country and profile.description
        assert profile.language in {"de", "en"}
        assert profile.timezone.startswith(("Europe/", "UTC"))


def test_oebb_profile_keeps_its_display_values():
    profile = get_profile("oebb")

    assert profile is not None
    assert profile.name == "ÖBB"
    assert profile.country == "Austria"
    assert profile.language == "de"
    assert profile.timezone == "Europe/Vienna"


def test_get_profile_is_case_insensitive():
    assert get_profile("OEBB") is PROFILES["oebb"]
    assert get_profile("Sbb") is PROFILES["sbb"]


def test_get_profile_of_an_unknown_provider_is_none():
    assert get_profile("sncf") is None


def test_every_profile_has_a_hafas_configuration():
    """A profile without an endpoint would fail at runtime, not at import."""
    missing = [key for key in PROFILES if PROFILES[key].hafas_profile_id not in HAFAS_CONFIGS]

    assert missing == []


def test_list_profiles_returns_plain_json_serialisable_dicts():
    profiles = list_profiles()

    assert len(profiles) == 4
    assert set(profiles[0]) == {"id", "name", "country", "description", "language"}
    # an MCP tool result has to survive serialisation
    json.dumps(profiles)


def test_list_profiles_names_the_current_profile_reference():
    entry = next(p for p in list_profiles() if p["id"] == "oebb")

    assert entry["name"] == "ÖBB"
    assert entry["country"] == "Austria"


@pytest.mark.parametrize("key", ["oebb", "db", "sbb", "ns"])
def test_profile_ids_are_lowercase_and_match_their_key(key):
    assert PROFILES[key].hafas_profile_id == key
