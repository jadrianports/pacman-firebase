import os
from paths import resource_path


def test_pixel_font_asset_present():
    path = resource_path("assets/fonts/PressStart2P-Regular.ttf")
    assert os.path.isfile(path), f"pixel font missing at {path}"
    assert os.path.getsize(path) > 10_000  # a real TTF, not an empty stub
