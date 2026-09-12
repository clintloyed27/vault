import io
import pytest


def test_spoofed_mime_type_rejected(client, auth_header_user_a):
    """File extension is .jpg but content is plain bash/python script."""
    fake_payload = b"#!/bin/bash\nrm -rf / --no-preserve-root\necho 'hacked'\n"
    res = client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": ("exploit.jpg", fake_payload, "image/jpeg")},
    )
    assert res.status_code == 422
    assert "unsupported or spoofed" in res.json()["detail"].lower()


def test_corrupted_image_rejected(client, auth_header_user_a):
    """Payload has JPEG signature but truncated corrupted image stream."""
    corrupted_payload = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb"
    res = client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": ("broken.jpg", corrupted_payload, "image/jpeg")},
    )
    assert res.status_code == 422


def test_path_traversal_filename_sanitized(client, auth_header_user_a, sample_jpeg_bytes):
    """Filename contains directory traversal attempts."""
    traversal_filename = "../../../../../etc/passwd.jpg"
    res = client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": (traversal_filename, sample_jpeg_bytes, "image/jpeg")},
    )
    assert res.status_code == 201
    image_data = res.json()[0]
    # Verify the stored filename is sanitized
    assert ".." not in image_data["original_filename"]
    assert "/" not in image_data["original_filename"]
    assert image_data["original_filename"].endswith(".jpg")


def test_successful_upload_creates_thumbnail_and_dimensions(
    client, auth_header_user_a, sample_jpeg_bytes
):
    res = client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": ("vacation.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    assert res.status_code == 201
    data = res.json()[0]
    assert data["width"] == 640
    assert data["height"] == 480
    assert data["mime_type"] == "image/jpeg"
    assert data["thumbnail_key"] is not None
    assert len(data["checksum_sha256"]) == 64

    # Verify thumbnail stream works
    thumb_res = client.get(f"/api/v1/images/{data['id']}/thumbnail", headers=auth_header_user_a)
    assert thumb_res.status_code == 200
    assert thumb_res.headers["content-type"] == "image/webp"
