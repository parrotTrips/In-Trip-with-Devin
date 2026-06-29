from __future__ import annotations

from datetime import timedelta
import os
from typing import Callable

import google.auth
from google.auth.transport.requests import Request
from google.cloud import storage


SignedUrlGenerator = Callable[[str, str, timedelta], str]


def parse_gcs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError("GCS URI must start with gs://")

    path = uri.removeprefix("gs://")
    bucket, separator, object_name = path.partition("/")
    if not bucket or not separator or not object_name:
        raise ValueError("GCS URI must include bucket and object path")

    return bucket, object_name


def generate_signed_url(bucket_name: str, object_name: str, expiration: timedelta) -> str:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = Request()
    credentials.refresh(request)

    service_account_email = (
        os.environ.get("SERVICE_ACCOUNT_EMAIL")
        or getattr(credentials, "service_account_email", None)
        or getattr(credentials, "signer_email", None)
    )
    if not service_account_email:
        raise RuntimeError("SERVICE_ACCOUNT_EMAIL is required to sign GCS service agreement URLs")

    client = storage.Client()
    blob = client.bucket(bucket_name).blob(object_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET",
        service_account_email=service_account_email,
        access_token=credentials.token,
    )


def resolve_service_agreement_url(
    service_agreement_url: str | None,
    *,
    signer: SignedUrlGenerator = generate_signed_url,
) -> str | None:
    if not service_agreement_url:
        return None

    if not service_agreement_url.startswith("gs://"):
        return service_agreement_url

    bucket_name, object_name = parse_gcs_uri(service_agreement_url)
    return signer(bucket_name, object_name, timedelta(minutes=30))
