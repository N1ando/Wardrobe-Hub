"""End-to-end API tests using synthetic silhouettes + the threshold backend."""

from tests.synthetic import front_array, side_array, to_png


def _files():
    return {
        "front": ("front.png", to_png(front_array()), "image/png"),
        "side": ("side.png", to_png(side_array()), "image/png"),
    }


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_measurements_happy_path(client):
    resp = client.post(
        "/api/v1/measurements",
        data={"height_value": "70", "height_unit": "in"},
        files=_files(),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["unit"] == "in"
    assert body["height"] == 70.0

    m = body["measurements"]
    # All three circumferences present, positive, and physically ordered
    # (hip widest, thigh smallest) for this figure.
    assert m["waist"] > 0 and m["low_hip"] > 0 and m["thigh"] > 0
    assert m["low_hip"] > m["thigh"]
    assert body["diagnostics"] is None


def test_debug_returns_overlays(client):
    resp = client.post(
        "/api/v1/measurements",
        data={"height_value": "70", "height_unit": "in", "debug": "true"},
        files=_files(),
    )
    assert resp.status_code == 200, resp.text
    diag = resp.json()["diagnostics"]
    assert diag is not None
    assert "overlays" in diag
    assert diag["overlays"]["front"] and diag["overlays"]["side"]
    # Front and side each get their own pixel-to-unit ratio.
    assert diag["front"]["ratio"] > 0 and diag["side"]["ratio"] > 0


def test_rejects_implausible_height(client):
    resp = client.post(
        "/api/v1/measurements",
        data={"height_value": "5", "height_unit": "in"},  # ~12.7 cm
        files=_files(),
    )
    assert resp.status_code == 422


def test_rejects_non_image_upload(client):
    files = {
        "front": ("front.txt", b"not an image", "text/plain"),
        "side": ("side.png", to_png(side_array()), "image/png"),
    }
    resp = client.post(
        "/api/v1/measurements",
        data={"height_value": "70", "height_unit": "in"},
        files=files,
    )
    assert resp.status_code == 422
