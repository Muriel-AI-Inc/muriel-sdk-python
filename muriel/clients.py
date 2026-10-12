"""Object-oriented clients matching the API documentation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import get_api_key
from .endpoints.requirements import get_requirements as _get_requirements
from .endpoints.results import get_results as _get_results
from .endpoints.systems import get_systems as _get_systems


class _BaseClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        resolved_key = api_key or token or get_api_key()
        if not resolved_key:
            raise ValueError("api_key or token is required, or set MURIEL_API_KEY")
        self.api_key = resolved_key
        self.base_url = base_url


class RequirementsClient(_BaseClient):
    """Client for sampling requirements endpoints."""

    def get_requirements(
        self,
        pwsid: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
        system_princ: Optional[str] = None,
    ) -> Dict[str, Any]:
        return _get_requirements(
            pwsid=pwsid,
            state=state,
            api_key=self.api_key,
            limit=limit,
            system_princ=system_princ,
            base_url=self.base_url,
        )


class SystemsClient(_BaseClient):
    """Client for public water system metadata."""

    def get_systems(
        self,
        state: str,
        limit: int = 100,
        system_princ: Optional[str] = None,
        system_statu: Optional[str] = None,
    ) -> Dict[str, Any]:
        return _get_systems(
            state=state,
            api_key=self.api_key,
            limit=limit,
            system_princ=system_princ,
            system_statu=system_statu,
            base_url=self.base_url,
        )


class SamplesClient(_BaseClient):
    """Client for sample results; wraps get_results() for messages-style parameters."""

    def get_samples(
        self,
        pwsid: Optional[str] = None,
        state: Optional[str] = None,
        analyte: Optional[str] = None,
        sample_date_start: Optional[str] = None,
        sample_date_end: Optional[str] = None,
        compliance_status: Optional[str] = None,
        limit: int = 100,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        if compliance_status is not None:
            kwargs["compliance_status"] = compliance_status

        return _get_results(
            pwsid=pwsid,
            state=state,
            analyte=analyte,
            start_date=sample_date_start,
            end_date=sample_date_end,
            api_key=self.api_key,
            num=limit,
            base_url=self.base_url,
            **kwargs,
        )
