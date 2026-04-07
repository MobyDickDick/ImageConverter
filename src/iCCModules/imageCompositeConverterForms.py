"""Formal geometry primitives (circle + handle) for ImageConverter."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RGBWert:
    """RGB value constrained to Nummer(256) semantics (0..255)."""

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for channel_name, channel in (("r", self.r), ("g", self.g), ("b", self.b)):
            if not isinstance(channel, int):
                raise TypeError(f"RGB channel '{channel_name}' must be an integer.")
            if channel < 0 or channel >= 256:
                raise ValueError(f"RGB channel '{channel_name}' must satisfy 0 <= x < 256.")

    def toHex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_hex(self) -> str:
        return self.toHex()


@dataclass(frozen=True)
class Punkt:
    x: float
    y: float


@dataclass(frozen=True)
class Kreis:
    mittelpunkt: Punkt
    radius: float
    randbreite: float
    rand_farbe: RGBWert
    hintergrundfarbe: RGBWert

    def __post_init__(self) -> None:
        if float(self.radius) <= 0:
            raise ValueError("Kreis.radius must be > 0.")
        if float(self.randbreite) < 0:
            raise ValueError("Kreis.randbreite must be >= 0.")
        if float(self.randbreite) > float(self.radius):
            raise ValueError("Constraint verletzt: Randbreite <= Radius.")


@dataclass(frozen=True)
class Griff:
    anfang: Punkt
    ende: Punkt

    @property
    def laenge(self) -> float:
        return abstand(self.anfang, self.ende)


@dataclass(frozen=True)
class Kelle:
    griff: Griff
    kreis: Kreis

    def __post_init__(self) -> None:
        if self.griff.anfang != self.kreis.mittelpunkt:
            raise ValueError("Constraint verletzt: Griff.Anfang == Kreis.Mittelpunkt.")
        if self.griff.laenge <= float(self.kreis.radius):
            raise ValueError("Constraint verletzt: Griff.Länge > Kreis.Radius.")

    def toSvg(self, width: int, height: int, *, clip_to_canvas: bool = True) -> str:
        """Render the ladle as SVG. Handle is drawn first (background), then circle."""
        handle_stroke = max(1.0, float(self.kreis.randbreite))
        cx = float(self.kreis.mittelpunkt.x)
        cy = float(self.kreis.mittelpunkt.y)
        radius = float(self.kreis.radius)
        handle = (
            f'<line x1="{self.griff.anfang.x:.2f}" y1="{self.griff.anfang.y:.2f}" '
            f'x2="{self.griff.ende.x:.2f}" y2="{self.griff.ende.y:.2f}" '
            f'stroke="{self.kreis.rand_farbe.toHex()}" stroke-width="{handle_stroke:.2f}" stroke-linecap="round"/>'
        )
        circle = (
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" '
            f'fill="{self.kreis.hintergrundfarbe.toHex()}" stroke="{self.kreis.rand_farbe.toHex()}" '
            f'stroke-width="{float(self.kreis.randbreite):.2f}"/>'
        )
        if not clip_to_canvas:
            body = f"{handle}{circle}"
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>'

        clip_id = "canvasClip"
        body = (
            f'<defs><clipPath id="{clip_id}"><rect x="0" y="0" width="{width}" height="{height}" /></clipPath></defs>'
            f'<g clip-path="url(#{clip_id})">{handle}{circle}</g>'
        )
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>'
    def to_svg(self, width: int, height: int, *, clip_to_canvas: bool = True) -> str:
        return self.toSvg(width, height, clip_to_canvas=clip_to_canvas)


def abstand(punkt1: Punkt, punkt2: Punkt) -> float:
    return math.hypot(float(punkt1.x) - float(punkt2.x), float(punkt1.y) - float(punkt2.y))


def buildOrientedKelle(
    orientation: str,
    *,
    mittelpunkt: Punkt,
    radius: float,
    griff_laenge: float,
    randbreite: float,
    rand_farbe: RGBWert,
    hintergrundfarbe: RGBWert,
) -> Kelle:
    """Create a Kelle with handle orientation in {left, right, top, bottom/down}."""
    orient = str(orientation).strip().lower()
    if orient in {"bottom", "down", "unten"}:
        endpunkt = Punkt(mittelpunkt.x, mittelpunkt.y + float(griff_laenge))
    elif orient in {"top", "up", "oben"}:
        endpunkt = Punkt(mittelpunkt.x, mittelpunkt.y - float(griff_laenge))
    elif orient in {"left", "links"}:
        endpunkt = Punkt(mittelpunkt.x - float(griff_laenge), mittelpunkt.y)
    elif orient in {"right", "rechts"}:
        endpunkt = Punkt(mittelpunkt.x + float(griff_laenge), mittelpunkt.y)
    else:
        raise ValueError("orientation must be one of: left, right, top/up, bottom/down")

    return Kelle(
        griff=Griff(anfang=mittelpunkt, ende=endpunkt),
        kreis=Kreis(
            mittelpunkt=mittelpunkt,
            radius=float(radius),
            randbreite=float(randbreite),
            rand_farbe=rand_farbe,
            hintergrundfarbe=hintergrundfarbe,
        ),
    )
