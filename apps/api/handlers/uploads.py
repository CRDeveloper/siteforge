"""POST /uploads/presign — generate S3 pre-signed upload URL."""
import boto3
import uuid
import os
import logging

from lib.response import ok, error

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def presign_upload(request: dict) -> dict:
    content_type = request["body"].get("contentType", "").strip()
    filename = request["body"].get("filename", "file").strip()
    user_id = request["user"]["userId"]

    if content_type not in ALLOWED_TYPES:
        return error(400, f"File type not allowed. Permitted: {', '.join(ALLOWED_TYPES)}")

    ext_map = {
        "image/jpeg": ".jpg", "image/png": ".png",
        "image/webp": ".webp", "application/pdf": ".pdf",
    }
    ext = ext_map.get(content_type, "")
    key = f"appointments/{user_id}/{uuid.uuid4()}{ext}"

    s3 = boto3.client("s3")
    try:
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": os.environ["UPLOADS_BUCKET"],
                "Key": key,
                "ContentType": content_type,
                "ContentLength": MAX_SIZE_BYTES,
            },
            ExpiresIn=300,  # 5 minutes
        )
        return ok({"uploadUrl": presigned_url, "key": key})
    except Exception as e:
        logger.error(f"presign error: {e}")
        return error(500, "Could not generate upload URL")
