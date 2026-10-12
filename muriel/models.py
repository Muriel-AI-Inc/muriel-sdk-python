"""Pydantic models for request/response validation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WaterQualityRecord(BaseModel):
    """Water quality test result record."""

    result_uuid: str = Field(description="Unique record identifier")
    state: str = Field(description="State abbreviation")
    pwsid: str = Field(description="Water system identifier")
    system_name: str = Field(description="Name of the water system")
    result_analyte_name: Optional[str] = Field(None, description="Chemical or test name")
    analyte_group: Optional[str] = Field(
        None, description="Regulatory category group (e.g., 'pfas', 'dbps', 'microbial')"
    )
    result_value: Optional[str] = Field(None, description="Test result value")
    result_unit: Optional[str] = Field(None, description="Unit of measurement")
    concentration_value: Optional[float] = Field(None, description="Numeric concentration value")
    concentration_units: Optional[str] = Field(None, description="Concentration units")
    result_non_detect: bool = Field(False, description="True if no concentration was detected")
    sample_collection_date: Optional[str] = Field(None, description="Sample collection date")
    result_laboratory: Optional[str] = Field(None, description="Testing laboratory")
    result_sample_point: Optional[str] = Field(None, description="Sampling point identifier")
    result_sample_location: Optional[str] = Field(None, description="Sampling location")
    result_facility_id: Optional[str] = Field(None, description="Facility identifier")
    result_latitude: Optional[float] = Field(None, description="Latitude of the sampling point")
    result_longitude: Optional[float] = Field(None, description="Longitude of the sampling point")
    result_address: Optional[str] = Field(None, description="Address of the sampling point")
    distance_miles: Optional[float] = Field(
        None, description="Distance from query point (for address-based queries)"
    )

    class Config:
        extra = "allow"


class GeocodingData(BaseModel):
    """Geocoding data for a facility or sampling point."""

    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Original address string")
    address_formatted: Optional[str] = Field(
        None, description="Formatted address from geocoding service"
    )
    source: Optional[str] = Field(None, description="Geocoding service source")
    confidence: Optional[int] = Field(None, description="Geocoding confidence score (0-100)")
    match_type: Optional[str] = Field(None, description="Match type")
    postcode: Optional[str] = Field(None, description="Postal code")
    county: Optional[str] = Field(None, description="County name")


class FacilityData(BaseModel):
    """Facility with geocoding data."""

    pwsid: str = Field(description="Water system identifier")
    system_name: Optional[str] = Field(None, description="Name of the water system")
    facility_state_assigned_id: str = Field(
        description="State-assigned facility identifier"
    )
    geocoding: Optional[GeocodingData] = Field(None, description="Geocoding data")


class SamplingPointData(BaseModel):
    """Sampling point with geocoding data."""

    pwsid: str = Field(description="Water system identifier")
    system_name: Optional[str] = Field(None, description="Name of the water system")
    sample_point: str = Field(description="Sampling point identifier")
    facility_state_assigned_id: Optional[str] = Field(
        None, description="State-assigned facility identifier"
    )
    geocoding: Optional[GeocodingData] = Field(None, description="Geocoding data")


class SystemRecordsResponse(BaseModel):
    """Response for system records query."""

    pwsid: str
    system_name: str
    state: str
    record_count: int
    records: List[WaterQualityRecord]
    limit: int


class StateRecordsResponse(BaseModel):
    """Response for state records query."""

    state: str
    record_count: int
    total_records: int
    records: List[WaterQualityRecord]
    limit: int


class StateFacilitiesResponse(BaseModel):
    """Response for state facilities query."""

    state: str
    facility_count: int
    facilities: List[FacilityData]
    limit: int


class StateSamplingPointsResponse(BaseModel):
    """Response for state sampling points query."""

    state: str
    sampling_point_count: int
    sampling_points: List[SamplingPointData]
    limit: int


class AgentQueryResponse(BaseModel):
    """What muriel.query() / Agent.query() return when no schema is given."""

    results: List[Dict[str, Any]] = Field(description="The records the agent's data tools returned")
    count: int = Field(description="len(results)")
    summary: str = Field(description="The agent's answer in plain English")
    execution_log: List[Dict[str, Any]] = Field(
        default_factory=list, description="Each tool the agent ran, with its input")
    warning: Optional[str] = Field(None, description="Set when the answer needs a caveat")
    documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Files the agent produced (CSV, PDF): filename, url, rows")
    credits: Optional[Dict[str, Any]] = Field(
        None, description="What the question cost (charged) and the balance afterwards")

    class Config:
        extra = "allow"
