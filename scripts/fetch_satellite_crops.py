"""
Satellite Target Crop Generator for Discovered Pre-600 BCE Sites.
Fetches high-resolution satellite imagery tiles (ESRI World Imagery),
stitches a multi-tile regional mosaic centered on prospective mound coordinates,
overlays archaeological target rings, geographic crosshairs, scale bars, and telemetry cards.

Outputs:
- results/candidates/satellite_crops/*.png
"""

from __future__ import annotations
import io
import math
from pathlib import Path
from typing import List, Tuple
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests


def latlon_to_tile(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """Convert latitude/longitude to Web Mercator tile x, y indices."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def tile_to_latlon(xtile: int, ytile: int, zoom: int) -> Tuple[float, float]:
    """Convert tile index to northwest corner latitude/longitude."""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def fetch_satellite_mosaic(
    lat: float,
    lon: float,
    zoom: int = 16,
    grid_radius: int = 1,
) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Fetch a (2*grid_radius + 1) x (2*grid_radius + 1) tile mosaic centered on (lat, lon).
    Returns (stitched_pil_image, (center_pixel_x, center_pixel_y)).
    """
    cx_tile, cy_tile = latlon_to_tile(lat, lon, zoom)
    tile_size = 256
    width_tiles = 2 * grid_radius + 1
    mosaic_w = width_tiles * tile_size
    mosaic_h = width_tiles * tile_size

    mosaic = Image.new("RGB", (mosaic_w, mosaic_h), color=(30, 30, 30))
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ArchaeologicalRemoteSensing/1.0"}

    # Exact pixel offset of target (lat, lon) within the center tile
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_exact = (lon + 180.0) / 360.0 * n
    y_exact = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

    pixel_offset_x = int((x_exact - cx_tile) * tile_size)
    pixel_offset_y = int((y_exact - cy_tile) * tile_size)

    center_px = (grid_radius * tile_size + pixel_offset_x, grid_radius * tile_size + pixel_offset_y)

    for dx in range(-grid_radius, grid_radius + 1):
        for dy in range(-grid_radius, grid_radius + 1):
            tx = cx_tile + dx
            ty = cy_tile + dy
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ty}/{tx}"
            try:
                r = requests.get(url, headers=headers, timeout=8)
                if r.status_code == 200:
                    tile_img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    paste_x = (dx + grid_radius) * tile_size
                    paste_y = (dy + grid_radius) * tile_size
                    mosaic.paste(tile_img, (paste_x, paste_y))
            except Exception:
                pass

    return mosaic, center_px


def annotate_satellite_crop(
    mosaic: Image.Image,
    center_px: Tuple[int, int],
    candidate_id: str,
    culture_name: str,
    probability: float,
    height_m: float,
    paleo_dist_km: float,
    lat: float,
    lon: float,
    gates_passed: int,
) -> Image.Image:
    """Draw archaeological crosshairs, target bounding ring, telemetry banner, and scale."""
    img = mosaic.copy()
    draw = ImageDraw.Draw(img)

    cx, cy = center_px
    # Target concentric rings
    color_ring = (239, 68, 68) if probability >= 0.95 else (249, 115, 22)
    radius_outer = 45
    radius_inner = 18

    # Outer target ring
    draw.ellipse([cx - radius_outer, cy - radius_outer, cx + radius_outer, cy + radius_outer], outline=color_ring, width=3)
    # Inner target ring
    draw.ellipse([cx - radius_inner, cy - radius_inner, cx + radius_inner, cy + radius_inner], outline=(255, 255, 255), width=2)
    # Target crosshairs
    draw.line([cx - radius_outer - 15, cy, cx - radius_inner, cy], fill=color_ring, width=2)
    draw.line([cx + radius_inner, cy, cx + radius_outer + 15, cy], fill=color_ring, width=2)
    draw.line([cx, cy - radius_outer - 15, cx, cy - radius_inner], fill=color_ring, width=2)
    draw.line([cx, cy + radius_inner, cx, cy + radius_outer + 15], fill=color_ring, width=2)

    # Top telemetry header box
    box_w, box_h = img.width, 110
    draw.rectangle([0, 0, box_w, box_h], fill=(15, 23, 42, 230))
    draw.line([0, box_h, box_w, box_h], fill=color_ring, width=3)

    # Text annotations
    title = f"{candidate_id} | PRE-600 BCE DISCOVERY TARGET"
    prob_str = f"CONFIDENCE: {probability*100:.1f}% (Tier 1 Ultra-High)" if probability >= 0.95 else f"CONFIDENCE: {probability*100:.1f}%"
    cult_str = f"PREDICTED CULTURE: {culture_name.upper()}"
    coords_str = f"GPS: {lat:.5f}° N, {lon:.5f}° E  |  ESTIMATED RELIEF: {height_m:.1f} m  |  PALEOCHANNEL: {paleo_dist_km:.2f} km"
    gates_str = f"7-EVIDENCE ORTHOGONAL GATES PASSED: {gates_passed} / 7 (Topography + BSI + SAR + Fluvial Prior + SOI Map + AlphaEarth)"

    # Simple clean rendering
    draw.text((16, 12), title, fill=(255, 255, 255))
    draw.text((16, 32), prob_str, fill=color_ring)
    draw.text((16, 50), cult_str, fill=(56, 189, 248))
    draw.text((16, 68), coords_str, fill=(226, 232, 240))
    draw.text((16, 86), gates_str, fill=(148, 163, 184))

    # Bottom scale bar (~200m at zoom 16 is approx 100 pixels in northern India)
    bar_x1, bar_y = img.width - 150, img.height - 25
    bar_x2 = bar_x1 + 100
    draw.line([bar_x1, bar_y, bar_x2, bar_y], fill=(255, 255, 255), width=4)
    draw.line([bar_x1, bar_y - 6, bar_x1, bar_y + 6], fill=(255, 255, 255), width=2)
    draw.line([bar_x2, bar_y - 6, bar_x2, bar_y + 6], fill=(255, 255, 255), width=2)
    draw.text((bar_x1 + 18, bar_y - 20), "200 meters", fill=(255, 255, 255))

    return img


def generate_all_satellite_crops(
    candidates_csv: Path | str = "results/candidates/undiscovered_pre600bce_candidates.csv",
    output_dir: Path | str = "results/candidates/satellite_crops",
    top_n: int = 5,
) -> List[Path]:
    """Generate high-resolution annotated satellite crops for top candidates."""
    df = pd.read_csv(candidates_csv)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    generated_paths: List[Path] = []
    top_candidates = df.head(top_n)

    for idx, row in top_candidates.iterrows():
        cid = str(row["candidate_id"])
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        prob = float(row["calibrated_probability"])
        cult = str(row["predicted_culture"])
        h = float(row["estimated_height_m"])
        p_dist = float(row["dist_paleochannel_km"])
        gates = int(row["evidence_gate_count"])

        print(f"Fetching satellite mosaic for {cid} ({lat:.4f}, {lon:.4f})...")
        mosaic, center_px = fetch_satellite_mosaic(lat, lon, zoom=16, grid_radius=1)
        annotated = annotate_satellite_crop(
            mosaic=mosaic,
            center_px=center_px,
            candidate_id=cid,
            culture_name=cult,
            probability=prob,
            height_m=h,
            paleo_dist_km=p_dist,
            lat=lat,
            lon=lon,
            gates_passed=gates,
        )

        crop_path = out / f"{cid}_satellite_crop.png"
        annotated.save(crop_path, format="PNG")
        generated_paths.append(crop_path)
        print(f"Saved: {crop_path.resolve()}")

    return generated_paths


if __name__ == "__main__":
    generate_all_satellite_crops()
