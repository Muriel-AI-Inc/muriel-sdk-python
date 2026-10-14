"""Muriel Python SDK - Official SDK for the Muriel® Water Quality API."""

from .client import MurielClient
from .agent import Agent, query
from .clients import RequirementsClient, SamplesClient, SystemsClient
from .endpoints.results import get_results
from .endpoints.facilities import (
    get_state_facilities,
    get_facility_geocoding,
)
from .endpoints.sampling_points import (
    get_state_sampling_points,
    get_sampling_point_geocoding,
)
from .endpoints.systems import get_systems
from .endpoints.requirements import get_requirements
from .endpoints.violations import get_violations
from .endpoints.contaminants import (
    get_latest,
    get_lead,
    get_pfas,
    get_coliform,
    get_nitrate,
    get_dbps,
    get_arsenic,
    get_manganese,
    get_vocs,
)
from .exceptions import (
    MurielAPIError,
    MurielAuthenticationError,
    MurielValidationError,
    MurielNotFoundError,
    MurielRateLimitError,
    MurielServerError,
    MurielCreditsError,
)

__version__ = "0.2.7"
__all__ = [
    # Client
    "MurielClient",
    "Agent",
    "query",
    "RequirementsClient",
    "SystemsClient",
    "SamplesClient",
    # Functions
    "get_results",
    "get_requirements",
    "get_violations",
    "get_systems",
    "get_state_facilities",
    "get_facility_geocoding",
    "get_state_sampling_points",
    "get_sampling_point_geocoding",
    # Contaminant convenience functions
    "get_latest",
    "get_lead",
    "get_pfas",
    "get_coliform",
    "get_nitrate",
    "get_dbps",
    "get_arsenic",
    "get_manganese",
    "get_vocs",
    # Exceptions
    "MurielAPIError",
    "MurielAuthenticationError",
    "MurielValidationError",
    "MurielNotFoundError",
    "MurielRateLimitError",
    "MurielServerError",
    "MurielCreditsError",
]
