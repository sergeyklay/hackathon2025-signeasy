import hashlib
import os
from dataclasses import dataclass
from datetime import datetime

from werkzeug.datastructures.file_storage import FileStorage


@dataclass
class UploadFileInfo:
    orig_filename: str
    content_type: str
    content_length: int
    filename: str
    sha256_content: str


class UploadManager:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder

    def save_file(self, file: FileStorage) -> UploadFileInfo:
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

        # TODO: Sanitize file.filename?
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + file.filename

        sha256_hash = hashlib.sha256()
        file_size = 0
        file.stream.seek(0)

        while chunk := file.stream.read(8192):
            sha256_hash.update(chunk)
            file_size += len(chunk)
        file.stream.seek(0)

        file_info = UploadFileInfo(
            orig_filename=file.filename,
            content_type=file.content_type,
            content_length=file_size,
            filename=filename,
            sha256_content=sha256_hash.hexdigest(),
        )

        # TODO: Check sha256_content to not upload the same content twice?
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        assert os.path.exists(filepath), f"Failed to upload file {file.filename}"

        return file_info
