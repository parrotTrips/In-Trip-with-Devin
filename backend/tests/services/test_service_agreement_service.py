from datetime import timedelta
from unittest.mock import Mock

import pytest

from app.services.service_agreement_service import (
    parse_gcs_uri,
    resolve_service_agreement_url,
)


def test_parse_gcs_uri_returns_bucket_and_object_name():
    bucket, object_name = parse_gcs_uri(
        "gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf"
    )

    assert bucket == "parrot-trips-service-agreements-prod"
    assert object_name == "trips/TEST-2026-FULL/service-agreement.pdf"


@pytest.mark.parametrize("uri", ["gs://", "gs://bucket-only", "gs:///object-only"])
def test_parse_gcs_uri_rejects_invalid_uri(uri):
    with pytest.raises(ValueError):
        parse_gcs_uri(uri)


def test_resolve_service_agreement_url_returns_none_for_empty_values():
    assert resolve_service_agreement_url(None) is None
    assert resolve_service_agreement_url("") is None


def test_resolve_service_agreement_url_keeps_regular_urls_unchanged():
    url = "https://example.com/service-agreement.pdf"

    assert resolve_service_agreement_url(url) == url


def test_resolve_service_agreement_url_generates_signed_url_for_gcs_uri():
    signer = Mock(return_value="https://storage.googleapis.com/signed-url")

    result = resolve_service_agreement_url(
        "gs://parrot-trips-service-agreements-prod/trips/TEST-2026-FULL/service-agreement.pdf",
        signer=signer,
    )

    assert result == "https://storage.googleapis.com/signed-url"
    signer.assert_called_once_with(
        "parrot-trips-service-agreements-prod",
        "trips/TEST-2026-FULL/service-agreement.pdf",
        timedelta(minutes=30),
    )

