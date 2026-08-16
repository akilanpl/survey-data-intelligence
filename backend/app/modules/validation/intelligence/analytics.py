from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ClusterProfile,
    DetectorConfig,
    DistrictProfile,
    EnumeratorProfile,
    QualityDetection,
    UnifiedRiskAssessment,
    ValidationRun,
)
from app.modules.dashboard.service import get_batch, latest_run
from app.modules.validation.intelligence.repository import list_detections
from app.modules.validation.intelligence.schemas import AnomalySummaryOut


def anomaly_summary(db: Session, batch_id: str | None) -> AnomalySummaryOut:
    batch = get_batch(db, batch_id)
    if batch is None:
        return AnomalySummaryOut()
    fusion = latest_run(db, batch.batch_id, "fusion")
    rows = []
    if fusion is not None:
        rows = list(
            db.scalars(
                select(UnifiedRiskAssessment).where(UnifiedRiskAssessment.validation_run_id == fusion.id)
            ).all()
        )
    detections = list_detections(db, batch.batch_id)
    intel_run = db.scalars(
        select(ValidationRun)
        .where(ValidationRun.batch_id == batch.batch_id, ValidationRun.validation_type == "intelligence")
        .order_by(ValidationRun.id.desc())
    ).first()
    meta = intel_run.skipped_rules_json if intel_run and isinstance(intel_run.skipped_rules_json, dict) else {}
    classes = Counter(
        (row.intelligence_classification or "INFORMATIONAL") for row in rows
    )
    by_detector = Counter(item.detector_type for item in detections)
    return AnomalySummaryOut(
        total=len(detections),
        high=sum(1 for item in detections if item.severity == "HIGH"),
        medium=sum(1 for item in detections if item.severity == "MEDIUM"),
        low=sum(1 for item in detections if item.severity in {"LOW", "NONE"}),
        validation_errors=classes.get("VALIDATION_ERROR", 0),
        unusual_patterns=classes.get("UNUSUAL_PATTERN", 0) + sum(1 for item in detections if item.classification == "UNUSUAL_PATTERN"),
        investigation_required=classes.get("INVESTIGATION_REQUIRED", 0),
        informational=classes.get("INFORMATIONAL", 0),
        by_detector=dict(by_detector),
        by_entity=dict(Counter(item.entity_type for item in detections)),
        detectors_available=list(meta.get("available") or []),
        detectors_skipped=list(meta.get("skipped") or []),
        skip_reasons=dict(meta.get("reason") or {}),
    )


def temporal_series(db: Session, batch_id: str | None) -> dict:
    batch = get_batch(db, batch_id)
    if batch is None:
        return {"available": False, "items": [], "message": "No batches available."}
    detections = [item for item in list_detections(db, batch.batch_id) if item.detector_type == "TEMPORAL_CHANGE"]
    items = [
        {
            "period": item.entity_id,
            "observed": item.observed_value,
            "baseline": item.expected_value,
            "threshold": (item.expected_value or 0) + 0.08,
            "deviation": item.deviation,
        }
        for item in detections
    ]
    skipped = anomaly_summary(db, batch.batch_id)
    available = "TEMPORAL" in skipped.detectors_available
    return {
        "available": available or bool(items),
        "batch_id": batch.batch_id,
        "items": items,
        "message": None if available or items else skipped.skip_reasons.get("TEMPORAL"),
    }


def enumerator_analytics(db: Session, enumerator_id: str, batch_id: str | None) -> dict:
    batch = get_batch(db, batch_id)
    if batch is None:
        return {"available": False, "message": "No batches available."}
    profile = db.scalars(
        select(EnumeratorProfile).where(
            EnumeratorProfile.batch_id == batch.batch_id,
            EnumeratorProfile.enumerator_id == enumerator_id,
        )
    ).first()
    detections = [
        item
        for item in list_detections(db, batch.batch_id)
        if item.enumerator_id == enumerator_id or (item.entity_type == "enumerator" and item.entity_id == enumerator_id)
    ]
    others = db.scalars(
        select(EnumeratorProfile).where(EnumeratorProfile.batch_id == batch.batch_id)
    ).all()
    comparison = []
    for row in others:
        means = (row.profile_json or {}).get("numeric_means") or {}
        comparison.append(
            {
                "enumerator_id": row.enumerator_id,
                "employment_rate": (row.profile_json or {}).get("employment_rate"),
                "mean_income": means.get("income"),
                "record_count": row.record_count,
                "highlight": row.enumerator_id == enumerator_id,
            }
        )
    return {
        "available": True,
        "batch_id": batch.batch_id,
        "enumerator_id": enumerator_id,
        "profile": None if profile is None else profile.profile_json,
        "detections": [
            {"detector_type": item.detector_type, "explanation": item.explanation, "observed": item.observed_value, "baseline": item.expected_value}
            for item in detections
        ],
        "comparison": comparison,
    }


def cluster_analytics(db: Session, cluster_id: str, batch_id: str | None) -> dict:
    batch = get_batch(db, batch_id)
    if batch is None:
        return {"available": False, "message": "No batches available."}
    profile = db.scalars(
        select(ClusterProfile).where(
            ClusterProfile.batch_id == batch.batch_id,
            ClusterProfile.cluster_id == cluster_id,
        )
    ).first()
    detections = [
        item
        for item in list_detections(db, batch.batch_id)
        if item.cluster_id == cluster_id or (item.entity_type == "cluster" and item.entity_id == cluster_id)
    ]
    return {
        "available": True,
        "batch_id": batch.batch_id,
        "cluster_id": cluster_id,
        "profile": None if profile is None else profile.profile_json,
        "detections": [
            {"detector_type": item.detector_type, "explanation": item.explanation, "observed": item.observed_value, "baseline": item.expected_value}
            for item in detections
        ],
    }


def district_analytics(db: Session, district_id: str, batch_id: str | None) -> dict:
    batch = get_batch(db, batch_id)
    if batch is None:
        return {"available": False, "message": "No batches available."}
    profile = db.scalars(
        select(DistrictProfile).where(
            DistrictProfile.batch_id == batch.batch_id,
            DistrictProfile.district_id == district_id,
        )
    ).first()
    detections = [
        item
        for item in list_detections(db, batch.batch_id)
        if item.district_id == district_id or (item.entity_type == "district" and item.entity_id == district_id)
    ]
    return {
        "available": True,
        "batch_id": batch.batch_id,
        "district_id": district_id,
        "profile": None if profile is None else profile.profile_json,
        "detections": [
            {"detector_type": item.detector_type, "explanation": item.explanation, "observed": item.observed_value, "baseline": item.expected_value}
            for item in detections
        ],
    }


def detector_analytics(db: Session, batch_id: str | None) -> dict:
    summary = anomaly_summary(db, batch_id)
    configs = list(db.scalars(select(DetectorConfig).order_by(DetectorConfig.category, DetectorConfig.detector_id)).all())
    return {
        "available": True,
        "summary": summary.model_dump(),
        "items": [{"detector": key, "count": value} for key, value in summary.by_detector.items()],
        "configs": [
            {
                "detector_id": row.detector_id,
                "name": row.name,
                "category": row.category,
                "enabled": row.enabled,
                "severity": row.severity,
                "description": row.description,
                "thresholds_json": row.thresholds_json,
            }
            for row in configs
        ],
    }


def distribution_analytics(db: Session, batch_id: str | None) -> dict:
    batch = get_batch(db, batch_id)
    if batch is None:
        return {"available": False, "items": []}
    detections = [item for item in list_detections(db, batch.batch_id) if item.detector_type == "DISTRIBUTION_SHIFT"]
    return {
        "available": True,
        "batch_id": batch.batch_id,
        "items": [
            {
                "field": item.field_name,
                "distance": item.observed_value,
                "threshold": item.expected_value,
                "explanation": item.explanation,
            }
            for item in detections
        ],
    }


def explorer(db: Session, batch_id: str | None, variable: str, level: str) -> dict:
    batch = get_batch(db, batch_id)
    if batch is None:
        return {"available": False, "items": []}
    model = {
        "district": DistrictProfile,
        "cluster": ClusterProfile,
        "enumerator": EnumeratorProfile,
    }.get(level or "district", DistrictProfile)
    rows = list(db.scalars(select(model).where(model.batch_id == batch.batch_id)).all())
    items = []
    for row in rows:
        payload = row.profile_json or {}
        means = payload.get("numeric_means") or {}
        entity_id = getattr(row, f"{level}_id", None) if level != "enumerator" else row.enumerator_id
        if level == "district":
            entity_id = row.district_id
        elif level == "cluster":
            entity_id = row.cluster_id
        items.append(
            {
                "id": entity_id,
                "record_count": row.record_count,
                "value": payload.get(variable) if variable in payload else means.get(variable),
                "employment_rate": payload.get("employment_rate"),
            }
        )
    values = [item["value"] for item in items if item["value"] is not None]
    national = sum(values) / len(values) if values else None
    return {
        "available": True,
        "batch_id": batch.batch_id,
        "variable": variable,
        "level": level,
        "national": national,
        "items": items,
    }
