"""文件操作 API"""
import mimetypes
import os
import tempfile
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import StorageSource, FileOperationLog, User
from app.schemas.schemas import FileListResponse, FileItem, FileOperationResponse
from app.services.factory import create_adapter
from app.services.base import BaseStorageAdapter

router = APIRouter(prefix="/files", tags=["文件操作"])


def _guess_media_type(path: str) -> str:
    return mimetypes.guess_type(path)[0] or "application/octet-stream"


def _inline_disposition(filename: str) -> str:
    quoted = quote(filename)
    return f"inline; filename*=UTF-8''{quoted}"


def _preview_headers(filename: str) -> dict:
    return {
        "Content-Disposition": _inline_disposition(filename),
        "X-Content-Type-Options": "nosniff",
    }


async def _stream_remote_preview(url: str, filename: str, request: Request):
    import httpx

    headers = {}
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    client = httpx.AsyncClient(follow_redirects=True, timeout=None)
    req = client.build_request("GET", url, headers=headers)
    resp = await client.send(req, stream=True)

    if resp.status_code not in (200, 206):
        await resp.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail="鑾峰彇鏂囦欢澶辫触")

    response_headers = _preview_headers(filename)
    for name in ("content-length", "content-range", "accept-ranges", "etag", "last-modified", "cache-control"):
        value = resp.headers.get(name)
        if value:
            response_headers[name] = value

    async def body():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    media_type = resp.headers.get("content-type") or _guess_media_type(filename)
    return StreamingResponse(
        body(),
        status_code=resp.status_code,
        media_type=media_type,
        headers=response_headers,
    )


async def _get_adapter(storage_id: int, db: AsyncSession):
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="存储源不存在")
    if not source.enabled:
        raise HTTPException(status_code=403, detail="存储源已禁用")
    config = dict(source.config)
    config["_storage_id"] = source.id
    return create_adapter(source.storage_type, config), source


async def _log_operation(db: AsyncSession, current_user: dict, source: StorageSource,
                         operation: str, file_path: str, file_name: str = "", file_size: int = 0,
                         request: Request = None):
    """记录操作日志"""
    # 获取客户端 IP
    ip_address = ""
    if request:
        # 优先从 X-Forwarded-For 获取（反向代理）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else ""
    
    log = FileOperationLog(
        user_id=current_user["user_id"],
        username=current_user.get("username", ""),
        storage_id=source.id,
        storage_name=source.name,
        operation=operation,
        file_path=file_path,
        file_name=file_name or os.path.basename(file_path),
        file_size=file_size,
        ip_address=ip_address,
    )
    db.add(log)


@router.get("/{storage_id}/list", response_model=FileListResponse)
async def list_files(
    storage_id: int,
    path: str = Query("/", description="目录路径"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    adapter, source = await _get_adapter(storage_id, db)
    files = await adapter.list_files(path)
    # Sort: dirs first, then by name
    files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
    return FileListResponse(files=files, path=path, storage_id=storage_id)


@router.get("/{storage_id}/dir-size")
async def get_dir_size(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """按需计算目录大小"""
    adapter, _ = await _get_adapter(storage_id, db)
    size = await _calc_dir_size(adapter, path)
    return {"path": path, "size": size}


async def _calc_dir_size(adapter, dir_path: str) -> int:
    """递归计算目录总大小"""
    total = 0
    try:
        items = await adapter.list_files(dir_path)
        for item in items:
            if item.is_dir:
                total += await _calc_dir_size(adapter, item.path)
            else:
                total += item.size or 0
    except Exception:
        pass
    return total


@router.get("/{storage_id}/info", response_model=FileItem)
async def get_file_info(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    adapter, _ = await _get_adapter(storage_id, db)
    return await adapter.get_file_info(path)


@router.get("/{storage_id}/download")
async def download_file(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)

    # Log download
    await _log_operation(db, current_user, source, "download", path, request=request)
    await db.commit()

    # For local storage, serve the file directly
    if source.storage_type == "local":
        real_path = adapter._real_path(path)
        if not os.path.isfile(real_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        filename = os.path.basename(real_path)
        return FileResponse(
            real_path,
            filename=filename,
            media_type=_guess_media_type(real_path),
            content_disposition_type="attachment",
            headers={"X-Content-Type-Options": "nosniff"},
        )

    # For cloud storage, redirect to signed URL
    url = await adapter.get_download_url(path)
    return {"url": url}


@router.get("/{storage_id}/preview")
async def preview_file(
    storage_id: int,
    path: str = Query(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    adapter, source = await _get_adapter(storage_id, db)
    filename = os.path.basename(path)

    if source.storage_type == "local":
        real_path = adapter._real_path(path)
        if not os.path.isfile(real_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            real_path,
            filename=os.path.basename(real_path),
            media_type=_guess_media_type(real_path),
            content_disposition_type="inline",
            headers={"X-Content-Type-Options": "nosniff"},
        )

    try:
        url = await adapter.get_download_url(path)
        return await _stream_remote_preview(url, filename, request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview proxy failed: {str(e)}")


@router.get("/{storage_id}/serve")
async def serve_local_file(
    storage_id: int,
    path: str = Query(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """Serve local files (used by local storage download URLs)"""
    result = await db.execute(select(StorageSource).where(StorageSource.id == storage_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404)
    if source.storage_type == "local":
        adapter = create_adapter("local", source.config)
        real_path = adapter._real_path(path)
        if not os.path.isfile(real_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        return FileResponse(real_path, filename=os.path.basename(real_path))
    # 云存储代理：下载后转发，避免 CORS
    config = dict(source.config)
    config["_storage_id"] = source.id
    adapter = create_adapter(source.storage_type, config)
    try:
        import tempfile
        url = await adapter.get_download_url(path)
        import httpx
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="获取文件失败")
            # 写入临时文件
            suffix = os.path.splitext(path)[1]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(resp.content)
            tmp.close()
            return FileResponse(tmp.name, filename=os.path.basename(path))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理失败: {str(e)}")


@router.post("/{storage_id}/upload", response_model=FileOperationResponse)
async def upload_file(
    storage_id: int,
    path: str = Query("/", description="目标目录"),
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)
    # Save uploaded file to temp
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        remote_path = BaseStorageAdapter.join_path(path, file.filename)
        result = await adapter.upload_file(tmp_path, remote_path)
        # Log
        await _log_operation(db, current_user, source, "upload", remote_path, file.filename, len(content), request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="上传成功", data=result.model_dump())
    except Exception as e:
        return FileOperationResponse(success=False, message=f"上传失败: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.delete("/{storage_id}/file", response_model=FileOperationResponse)
async def delete_file(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)
    try:
        await adapter.delete_file(path)
        await _log_operation(db, current_user, source, "delete", path, request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="删除成功")
    except Exception as e:
        return FileOperationResponse(success=False, message=f"删除失败: {str(e)}")


@router.delete("/{storage_id}/folder", response_model=FileOperationResponse)
async def delete_folder(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)
    try:
        # 检查文件夹是否为空
        contents = await adapter.list_files(path)
        if contents:
            return FileOperationResponse(
                success=False,
                message="文件夹不为空，请先清空文件夹内的所有内容后再删除"
            )
        await adapter.delete_folder(path)
        await _log_operation(db, current_user, source, "delete", path, request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="文件夹已删除")
    except Exception as e:
        return FileOperationResponse(success=False, message=f"删除失败: {str(e)}")


@router.post("/{storage_id}/mkdir", response_model=FileOperationResponse)
async def create_folder(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)
    try:
        await adapter.create_folder(path)
        await _log_operation(db, current_user, source, "mkdir", path, request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="文件夹创建成功")
    except Exception as e:
        return FileOperationResponse(success=False, message=f"创建失败: {str(e)}")


@router.post("/{storage_id}/move", response_model=FileOperationResponse)
async def move_file(
    storage_id: int,
    src_path: str = Query(...),
    dest_path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)
    try:
        await adapter.move_file(src_path, dest_path)
        await _log_operation(db, current_user, source, "move", src_path, request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="移动成功")
    except Exception as e:
        return FileOperationResponse(success=False, message=f"移动失败: {str(e)}")


@router.post("/{storage_id}/copy", response_model=FileOperationResponse)
async def copy_file(
    storage_id: int,
    src_path: str = Query(...),
    dest_path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    adapter, source = await _get_adapter(storage_id, db)
    try:
        await adapter.copy_file(src_path, dest_path)
        await _log_operation(db, current_user, source, "copy", src_path, request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="复制成功")
    except Exception as e:
        return FileOperationResponse(success=False, message=f"复制失败: {str(e)}")


@router.post("/{storage_id}/rename", response_model=FileOperationResponse)
async def rename_file(
    storage_id: int,
    path: str = Query(...),
    new_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),

    request: Request = None,
):
    """重命名文件/文件夹"""
    adapter, source = await _get_adapter(storage_id, db)
    try:
        parent = "/".join(path.rstrip("/").split("/")[:-1]) or "/"
        dest_path = BaseStorageAdapter.join_path(parent, new_name)
        await adapter.move_file(path, dest_path)
        await _log_operation(db, current_user, source, "rename", path, new_name, request=request)
        await db.commit()
        return FileOperationResponse(success=True, message="重命名成功")
    except Exception as e:
        return FileOperationResponse(success=False, message=f"重命名失败: {str(e)}")


@router.get("/{storage_id}/direct-link")
async def get_direct_link(
    storage_id: int,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取文件直链"""
    adapter, source = await _get_adapter(storage_id, db)
    try:
        url = await adapter.get_download_url(path, expires=86400)
        return {"url": url, "expires": 86400}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取直链失败: {str(e)}")


@router.get("/{storage_id}/search")
async def search_files(
    storage_id: int,
    keyword: str = Query(..., min_length=1),
    path: str = Query("/"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    adapter, _ = await _get_adapter(storage_id, db)
    # Simple recursive search (max depth 5, max 100 results)
    results = []

    async def _search(dir_path: str, depth: int):
        if depth > 5 or len(results) >= 100:
            return
        try:
            files = await adapter.list_files(dir_path)
        except:
            return
        for f in files:
            if keyword.lower() in f.name.lower():
                results.append(f)
                if len(results) >= 100:
                    return
            if f.is_dir:
                await _search(f.path, depth + 1)

    await _search(path, 0)
    return {"files": results, "keyword": keyword, "count": len(results)}
