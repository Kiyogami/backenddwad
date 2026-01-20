from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from typing import Annotated
import os

from storage_service import SupabaseStorageService
from supabase_client import get_supabase_client


router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def get_storage_service() -> SupabaseStorageService:
    client = get_supabase_client()
    return SupabaseStorageService(client)


@router.post("/video")
async def upload_verification_video(
    file: Annotated[UploadFile, File(...)],
    storage: SupabaseStorageService = Depends(get_storage_service),
):
    """Przyjmuje plik wideo (mp4/webm) i wrzuca go do Supabase Storage.

    Zwraca URL, który potem można zapisać przy zamówieniu / weryfikacji.
    """

    allowed_content_types = ["video/mp4", "video/webm", "video/quicktime"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowy typ pliku. Dozwolone: mp4, webm, mov.",
        )

    allowed_ext = [".mp4", ".webm", ".mov"]
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowe rozszerzenie pliku.",
        )

    data = await file.read()
    max_size = 100 * 1024 * 1024  # 100 MB
    if len(data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Plik jest za duży (max 100 MB).",
        )

    url = storage.upload_file(
        file_content=data,
        file_name=file.filename or "video.webm",
        content_type=file.content_type or "video/webm",
    )

    return {
        "success": True,
        "fileUrl": url,
        "fileName": file.filename,
        "fileSize": len(data),
    }
