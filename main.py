import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
import aiofiles

app = FastAPI()

# ----- Configuration and Setup -----
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# In-memory file status store.
# In production, use a persistent datastore to track file upload statuses.
file_statuses = {}  # key: file_id, value: {"last_byte": int, "complete": bool, "updated_at": datetime.utcnow()}

# ----- File Chunk Upload Endpoint -----
@app.post("/upload_chunk/{file_id}")
async def upload_chunk(
    file_id: str,
    file: UploadFile = File(...),
    start_byte: int = Header(...),
    end_byte: int = Header(...),
    checksum: int = Header(...)
):
    # Read the incoming chunk content.
    content = await file.read()

    # Verify checksum: sum of bytes modulo 256.
    calculated_checksum = sum(content) % 256
    if calculated_checksum != checksum:
        raise HTTPException(status_code=400, detail="Checksum validation failed")

    file_path = os.path.join(UPLOAD_DIR, file_id)
    # Open the file for random access; create if it doesn't exist.
    mode = "r+b" if os.path.exists(file_path) else "wb"
    async with aiofiles.open(file_path, mode) as f:
        await f.seek(start_byte)
        await f.write(content)

    # Update or create the file's status metadata.
    status = file_statuses.get(file_id, {"last_byte": 0, "complete": False, "updated_at": datetime.utcnow()})
    status["last_byte"] = max(status["last_byte"], end_byte)
    status["updated_at"] = datetime.utcnow()
    file_statuses[file_id] = status

    return {"message": "Chunk uploaded successfully", "file_id": file_id, "last_byte": status["last_byte"]}

# ----- File Status Monitoring Endpoint -----
@app.get("/file_status/{file_id}")
async def get_file_status(file_id: str):
    status = file_statuses.get(file_id)
    if not status:
        return {"file_id": file_id, "status": "not found"}
    file_state = "complete" if status.get("complete") else "partial"
    return {"file_id": file_id, "status": file_state, "last_byte": status.get("last_byte")}

# ----- Partial File Download Endpoint -----
@app.get("/download/{file_id}")
async def download_file(file_id: str, request: Request):
    file_path = os.path.join(UPLOAD_DIR, file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range")
    if range_header:
        try:
            # Expected format: "bytes=START-END"
            range_value = range_header.strip().split("=")[1]
            start_str, end_str = range_value.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Range header format")

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                bytes_to_send = end - start + 1
                while bytes_to_send > 0:
                    chunk = f.read(min(1024 * 1024, bytes_to_send))
                    if not chunk:
                        break
                    bytes_to_send -= len(chunk)
                    yield chunk

        headers = {"Content-Range": f"bytes {start}-{end}/{file_size}"}
        return StreamingResponse(iter_file(), status_code=206, headers=headers, media_type="application/octet-stream")
    else:
        # If no Range header is provided, stream the entire file.
        def iter_file():
            with open(file_path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    yield chunk
        return StreamingResponse(iter_file(), media_type="application/octet-stream")

# ----- Background Cleanup Task -----
def cleanup_old_uploads(expiration_minutes: int = 60):
    now = datetime.utcnow()
    expired_files = []
    for file_id, status in list(file_statuses.items()):
        updated_at = status.get("updated_at")
        if updated_at and (now - updated_at).total_seconds() > expiration_minutes * 60:
            expired_files.append(file_id)
    # Remove expired metadata; in production, you might archive or remove these files.
    for file_id in expired_files:
        del file_statuses[file_id]
        # Optionally, remove the file from disk or persist incomplete uploads.
    print(f"Cleaned up expired uploads: {expired_files}")

@app.post("/trigger_cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    background_tasks.add_task(cleanup_old_uploads)
    return {"message": "Cleanup task has been scheduled"}

@app.get("/")
async def root():
    return {"message": "Welcome to the File Handling API"}
