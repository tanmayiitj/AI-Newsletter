"""Job listing model and related enumerations."""

from enum import Enum

from pydantic import BaseModel, Field


class LocationType(str, Enum):
    """Job location type."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class ExperienceTier(str, Enum):
    """Job experience tier."""

    ONE_TO_TWO = "1-2yr"
    TWO_TO_FOUR = "2-4yr"


class JobListing(BaseModel):
    """A job posting within the jobs board section."""

    role_title: str = Field(..., min_length=1, max_length=150)
    company_name: str = Field(..., min_length=1, max_length=150)
    location_type: LocationType
    experience_tier: ExperienceTier
    description: str = Field(..., min_length=1, max_length=500)
    apply_url: str = Field(..., min_length=1)
