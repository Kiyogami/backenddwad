import os
import uuid
from typing import Optional

from fastapi import HTTPException, status
from supabase import Client


class SupabaseStorageService:
    """Simple wrapper around Supabase Storage for file uploads.

    We only use it as object storage (e.g. verification videos).
    """

    def __init__(self, client: Client) -> None:
        self.client = client
        self.bucket_name = os.environ.get("SUPABASE_STORAGE_BUCKET", "uploads")

    def upload_file(
        self,
        *,
        file_content: bytes,
        file_name: str,
        content_type: str,
        folder_path: str = "verification-videos",
    ) -> str:
        """Upload file to Supabase Storage and return public URL.

        In future we can switch to signed URLs if bucket is private.
        """
        try:
            ext = file_name.split(".")[-1] if "." in file_name else ""
            unique_id = str(uuid.uuid4())
            unique_name = f"{unique_id}.{ext}" if ext else unique_id
            full_path = f"{folder_path}/{unique_name}"

            resp = self.client.storage.from_(self.bucket_name).upload(
                path=full_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",
                    "upsert": False,
                },
            )

            # supabase-py returns a Response-like object; 200 == success
            if getattr(resp, "status_code", 200) >= 300:
                # Try to extract error message if present
                detail = "Upload failed"
                try:
                    data = resp.json()
                    detail = data.get("message", detail)
                except Exception:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=detail,
                )

            # For now we use public URL helper (works for public buckets)
            url = self.client.storage.from_(self.bucket_name).get_public_url(full_path)
            return url
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - generic safety net
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading file to storage: {exc}",
            )
