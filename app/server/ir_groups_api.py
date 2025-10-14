"""FastAPI service exposing the IR functional-group classifier."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Mapping, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from ml import IRGroupClassifier


class SpectrumPayload(BaseModel):
    """Request body describing an IR spectrum."""

    wavenumber_cm_1: Optional[List[float]] = Field(
        None, description="Wavenumber samples in cm^-1"
    )
    wavelength_nm: Optional[List[float]] = Field(
        None, description="Wavelength samples in nm (will be converted to cm^-1)"
    )
    intensity: List[float] = Field(..., description="Intensity or absorbance samples")
    normalise: bool = Field(
        True,
        description="Apply baseline correction and unit scaling prior to inference",
    )

    def to_classifier_payload(self) -> Mapping[str, object]:
        payload: Mapping[str, object] = {
            "intensity": self.intensity,
        }
        if self.wavenumber_cm_1 is not None:
            payload = {**payload, "wavenumber": self.wavenumber_cm_1}
        elif self.wavelength_nm is not None:
            payload = {**payload, "wavelengths": self.wavelength_nm}
        else:
            raise ValueError("Request must include wavenumber_cm_1 or wavelength_nm")
        return payload


class FunctionalGroupResponse(BaseModel):
    name: str
    probability: float
    threshold: float
    present: bool


class IRGroupResponse(BaseModel):
    backend: str
    predictions: List[FunctionalGroupResponse]


router = APIRouter()


@lru_cache(maxsize=4)
def _cached_classifier(normalise: bool = True) -> IRGroupClassifier:
    return IRGroupClassifier(normalise=normalise)


@router.post("/api/ir-groups", response_model=IRGroupResponse)
def identify_ir_groups(payload: SpectrumPayload) -> IRGroupResponse:
    """Run the IR functional-group classifier and return structured predictions."""

    classifier = _cached_classifier(payload.normalise)
    try:
        spectrum = payload.to_classifier_payload()
        predictions = classifier.predict_groups(spectrum)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IRGroupResponse(
        backend=classifier.backend_name,
        predictions=[
            FunctionalGroupResponse(
                name=item.name,
                probability=item.probability,
                threshold=item.threshold,
                present=item.present,
            )
            for item in predictions
        ]
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Spectra App IR groups API")
    app.include_router(router)
    return app


app = create_app()


__all__ = ["app", "create_app", "identify_ir_groups"]
