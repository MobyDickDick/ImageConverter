"""Reject embedded rasters and the retired per-pixel strip SVG encoding."""
import re


def pixel_copy_reason(root):
    if any(node.tag.rsplit('}', 1)[-1] == 'image' for node in root.iter()):
        return 'embedded_raster'
    # Identify the old geometry even when the job metadata has been lost.
    strip = re.compile(r'M\s*\d+\s+\d+\s*h\s*\d+\s*v\s*1\s*h\s*-\d+\s*z', re.I)
    runs = sum(len(strip.findall(node.get('d', ''))) for node in root.iter()
               if node.tag.rsplit('}', 1)[-1] == 'path')
    return 'pixel_trace' if runs >= 8 else ''
