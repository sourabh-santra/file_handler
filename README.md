# File Handler API

A FastAPI-based backend service that supports chunked file uploads, partial file downloads, upload progress tracking, and cleanup of stale uploads.

## Repository

GitHub: [sourabh-santra/file_handler](https://github.com/sourabh-santra/file_handler)

---

## Features

- Upload files in chunks
- Resume uploads and check upload progress
- Download files (fully or partially via Range headers)
- Cleanup old/stale uploads
- Swagger UI for easy testing
- Simple to extend with JWT authentication (optional, built-in)

---

## Setup Instructions


```bash
git clone https://github.com/sourabh-santra/file_handler.git
cd file_handler

python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate

pip install -r requirements.txt


uvicorn main:app --reload


Testing Using Swagger UI 


http://127.0.0.1:8000/docs


API Endpoints
Method	Endpoint	Description
POST	/upload_chunk/{file_id}	Uploads a file chunk
GET	/file_status/{file_id}	Returns upload status
GET	/download/{file_id}	Downloads a full or partial file
POST	/trigger_cleanup	Cleans up stale uploads
