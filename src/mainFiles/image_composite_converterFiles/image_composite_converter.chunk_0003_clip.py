


def _clip(value, low, high):
    """Clip scalar/array values without hard-requiring numpy at runtime."""
    if np is not None:
        return np.clip(value, low, high)
    if isinstance(value, (int, float)):
        return Action._clip_scalar(float(value), float(low), float(high))
    raise RuntimeError("numpy is required for non-scalar clip operations")





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

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


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
