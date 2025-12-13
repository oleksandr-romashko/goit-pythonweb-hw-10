"""Module for validating files and their properties."""

from typing import Set, BinaryIO

from pathlib import Path

from fastapi import UploadFile

from src.utils.constants import (
    MESSAGE_ERROR_EMPTY_UPLOAD_FILE,
    MESSAGE_ERROR_UNSUPPORTED_X_ERROR_TEMPLATE,
    MESSAGE_ERROR_FILE_TOO_LARGE_ERROR_TEMPLATE,
)


class FileValidationError(Exception):
    """Base file validation error."""


class UnsupportedMimeTypeValidationError(FileValidationError):
    """Raised when the file MIME type is unsupported."""


class UnsupportedFileTypeValidationError(FileValidationError):
    """Raised when the file type is unsupported."""


class EmptyFileValidationError(FileValidationError):
    """Raised when the file is empty."""


class TooLargeFileValidationError(FileValidationError):
    """Raised when the file is too large."""


class TooSmallFileValidationError(FileValidationError):
    """Raised when the file is too small."""


# TODO: Additionally add check of file structure, e.g. using Pillow (PIL.Image) / python-magic:
# * to check if file is really an image and not some renamed executable, etc.
# * to do so before file uploading
# * not to rely on provider validations only
# TODO: Add virus/malware scanning using some library or external service (ClamAV / external API)?


def validate_file_mime_type(file: UploadFile, allowed_mime_types: Set[str]) -> None:
    """
    Validate the MIME type of a file.

    Raises:
        UnsupportedFileMimeTypeValidationError:
            Raised when the file's MIME type is not in the allowed MIME types.
    """
    content_type = file.content_type or ""
    if content_type not in allowed_mime_types:
        raise UnsupportedMimeTypeValidationError(
            MESSAGE_ERROR_UNSUPPORTED_X_ERROR_TEMPLATE.format(
                subject="avatar MIME type",
                provided=content_type,
                supported=", ".join(sorted(allowed_mime_types)),
            )
        )


def validate_file_extension(file: UploadFile, allowed_file_ext: Set[str]) -> None:
    """
    Validate the file extension.

    Raises:
        UnsupportedFileTypeValidationError:
            Raised when the extension is not in the allowed file extension.
    """
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in allowed_file_ext:
        raise UnsupportedFileTypeValidationError(
            MESSAGE_ERROR_UNSUPPORTED_X_ERROR_TEMPLATE.format(
                subject="avatar file type",
                provided=ext,
                supported=", ".join(allowed_file_ext),
            )
        )


def validate_file_size(
    file: UploadFile, max_allowed_size: int, min_allowed_size: int = 0
) -> None:
    """
    Validate the file size in bytes.

    Raises:
        EmptyFileValidationError
            Raised when the file is empty (zero size).
        TooLargeFileValidationError:
            Raised when the file is too large.
        TooSmallFileValidationError:
            Raised when the file is too small.
    """
    stream: BinaryIO = file.file
    stream.seek(0, 2)  # Move cursor to the file end (2 = offset from the file end)
    size = stream.tell()  # Get current cursor position (file size in bytes)
    stream.seek(
        0
    )  # Reset cursor to the file start (otherwise empty file will be uploaded)

    if size == 0:
        raise EmptyFileValidationError(MESSAGE_ERROR_EMPTY_UPLOAD_FILE)

    if size > max_allowed_size:
        raise TooLargeFileValidationError(
            MESSAGE_ERROR_FILE_TOO_LARGE_ERROR_TEMPLATE.format(
                size=size,
                max_allowed_size=max_allowed_size,
            )
        )

    if min_allowed_size and size < min_allowed_size:
        raise TooSmallFileValidationError(
            f"File is too small: {size} bytes. Minimum allowed is {min_allowed_size} bytes."
        )
