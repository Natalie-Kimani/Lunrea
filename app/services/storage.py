"""File storage for uploaded media.

Two backends, chosen automatically:

* Cloudflare R2 (S3-compatible) when R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
  R2_SECRET_ACCESS_KEY and R2_BUCKET are all set. Used in production.
* Local disk (<project>/uploads/memories) otherwise. Used in development.

What gets saved in `media.file_path`:

* R2 files:    "r2:memories/<uuid>.<ext>"
* Local files: "uploads/memories/<uuid>.<ext>"   (the original format)

Because old rows keep their original format, existing local uploads keep
working after you switch on R2.
"""

import os

from flask import current_app

R2_PREFIX = "r2:"


def r2_enabled():
    return all(
        os.getenv(name)
        for name in (
            "R2_ACCOUNT_ID",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_BUCKET",
        )
    )


def _client():
    import boto3
    from botocore.config import Config as BotoConfig

    return boto3.client(
        "s3",
        # R2_ENDPOINT_URL is optional (tests, MinIO). Normally derived from the account id.
        endpoint_url=os.getenv("R2_ENDPOINT_URL")
        or f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def _project_root():
    return os.path.abspath(os.path.join(current_app.root_path, ".."))


def _local_dir():
    return os.path.join(_project_root(), "uploads", "memories")


def save_upload(file_storage, safe_filename, content_type=None):
    """Store an uploaded file and return the value to put in media.file_path."""
    if r2_enabled():
        key = f"memories/{safe_filename}"
        extra = {"ContentType": content_type} if content_type else {}
        file_storage.stream.seek(0)
        _client().upload_fileobj(
            file_storage.stream,
            os.environ["R2_BUCKET"],
            key,
            ExtraArgs=extra,
        )
        return R2_PREFIX + key

    os.makedirs(_local_dir(), exist_ok=True)
    full_path = os.path.join(_local_dir(), safe_filename)
    file_storage.save(full_path)
    return os.path.relpath(full_path, _project_root())


def delete_file(stored_path):
    """Remove a stored file. Never raises: cleanup must not hide the real error."""
    try:
        if stored_path.startswith(R2_PREFIX):
            _client().delete_object(
                Bucket=os.environ["R2_BUCKET"],
                Key=stored_path[len(R2_PREFIX):],
            )
        else:
            full_path = os.path.join(_project_root(), stored_path)
            if os.path.isfile(full_path):
                os.remove(full_path)
    except Exception:
        current_app.logger.exception("Could not delete stored file %s", stored_path)


def is_remote(stored_path):
    return stored_path.startswith(R2_PREFIX)


def open_remote(stored_path):
    """Return the boto3 get_object response for an R2 file (raises if missing)."""
    return _client().get_object(
        Bucket=os.environ["R2_BUCKET"],
        Key=stored_path[len(R2_PREFIX):],
    )


def local_path(stored_path):
    """Absolute path for a locally stored file, or None if it is outside uploads/."""
    full_path = os.path.abspath(os.path.join(_project_root(), stored_path))
    uploads_root = os.path.join(_project_root(), "uploads") + os.sep
    return full_path if full_path.startswith(uploads_root) else None
