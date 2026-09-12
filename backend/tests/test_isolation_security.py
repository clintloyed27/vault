import pytest


def test_cross_user_isolation_image_access(
    client, auth_header_user_a, auth_header_user_b, sample_jpeg_bytes
):
    # 1. User A uploads image A
    upload_res = client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": ("private_image_a.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    assert upload_res.status_code == 201
    image_a = upload_res.json()[0]
    image_a_id = image_a["id"]

    # 2. User A CAN access their own image
    get_a_res = client.get(f"/api/v1/images/{image_a_id}", headers=auth_header_user_a)
    assert get_a_res.status_code == 200
    assert get_a_res.json()["id"] == image_a_id

    # 3. User B attempts GET metadata for image A -> MUST FAIL (403 or 404)
    get_b_res = client.get(f"/api/v1/images/{image_a_id}", headers=auth_header_user_b)
    assert get_b_res.status_code in (403, 404)

    # 4. User B attempts GET file stream for image A -> MUST FAIL
    file_b_res = client.get(f"/api/v1/images/{image_a_id}/file", headers=auth_header_user_b)
    assert file_b_res.status_code in (403, 404)

    # 5. User B attempts GET thumbnail for image A -> MUST FAIL
    thumb_b_res = client.get(f"/api/v1/images/{image_a_id}/thumbnail", headers=auth_header_user_b)
    assert thumb_b_res.status_code in (403, 404)

    # 6. User B attempts DOWNLOAD image A -> MUST FAIL
    dl_b_res = client.get(f"/api/v1/images/{image_a_id}/download", headers=auth_header_user_b)
    assert dl_b_res.status_code in (403, 404)

    # 7. User B attempts DELETE image A -> MUST FAIL
    del_b_res = client.delete(f"/api/v1/images/{image_a_id}", headers=auth_header_user_b)
    assert del_b_res.status_code in (403, 404)

    # 8. Verify Image A is still present and owned by User A
    verify_res = client.get(f"/api/v1/images/{image_a_id}", headers=auth_header_user_a)
    assert verify_res.status_code == 200


def test_cross_user_album_isolation(
    client, auth_header_user_a, auth_header_user_b, sample_jpeg_bytes
):
    # 1. User A uploads Image A
    upload_res = client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": ("alice_pic.jpg", sample_jpeg_bytes, "image/jpeg")},
    )
    image_a_id = upload_res.json()[0]["id"]

    # 2. User A creates Album A
    album_a_res = client.post(
        "/api/v1/albums/",
        headers=auth_header_user_a,
        json={"title": "Alice Secret Album", "description": "Top secret"},
    )
    assert album_a_res.status_code == 201
    album_a_id = album_a_res.json()["id"]

    # 3. User B creates Album B
    album_b_res = client.post(
        "/api/v1/albums/",
        headers=auth_header_user_b,
        json={"title": "Bob Public Album"},
    )
    assert album_b_res.status_code == 201
    album_b_id = album_b_res.json()["id"]

    # 4. User B attempts to access Album A -> MUST FAIL
    get_album_b = client.get(f"/api/v1/albums/{album_a_id}", headers=auth_header_user_b)
    assert get_album_b.status_code in (403, 404)

    # 5. User B attempts to add User A's Image to Album B -> MUST FAIL with 403
    add_image_res = client.post(
        f"/api/v1/albums/{album_b_id}/images",
        headers=auth_header_user_b,
        json={"image_ids": [image_a_id]},
    )
    assert add_image_res.status_code == 403

    # 6. User B attempts to DELETE Album A -> MUST FAIL
    del_album_res = client.delete(f"/api/v1/albums/{album_a_id}", headers=auth_header_user_b)
    assert del_album_res.status_code in (403, 404)


def test_user_gallery_listing_isolation(
    client, auth_header_user_a, auth_header_user_b, sample_jpeg_bytes, sample_png_bytes
):
    # User A uploads 1 image
    client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_a,
        files={"files": ("alice.jpg", sample_jpeg_bytes, "image/jpeg")},
    )

    # User B uploads 2 images
    client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_b,
        files={
            "files": ("bob1.png", sample_png_bytes, "image/png"),
        },
    )
    client.post(
        "/api/v1/images/upload",
        headers=auth_header_user_b,
        files={
            "files": ("bob2.png", sample_png_bytes, "image/png"),
        },
    )

    # User A listing contains strictly 1 image
    list_a = client.get("/api/v1/images/", headers=auth_header_user_a).json()
    assert list_a["total"] == 1
    assert list_a["items"][0]["original_filename"] == "alice.jpg"

    # User B listing contains strictly 2 images
    list_b = client.get("/api/v1/images/", headers=auth_header_user_b).json()
    assert list_b["total"] == 2
    for item in list_b["items"]:
        assert "bob" in item["original_filename"]
