from dataclasses import dataclass, fields
from app.render.render_contract import Color


@dataclass(frozen=True)
class Theme:
    """Named palette keyed by semantic roles (not free-floating colours)."""

    name: str
    background: Color
    text: Color
    text_highlight: Color
    wall: Color
    cell_floor: Color
    trail: Color
    head: Color
    entry: Color
    exit: Color
    solution: Color
    pattern: Color

    def validate(self, min_contrast: float = 4.5) -> None:
        """Raise ValueError if text / background contrast is too low."""
        text_contrast = contrast_ratio(self.text, self.background)
        text_highlight_contrast = contrast_ratio(self.text_highlight,
                                                 self.background)
        if text_contrast < min_contrast:
            raise ValueError("Text contrast ratio is too low: "
                             f"{text_contrast}")
        if text_highlight_contrast < min_contrast:
            raise ValueError("Text highlight contrast ratio is too low: "
                             f"{text_highlight_contrast}")


def contrast_ratio(fg: Color, bg: Color) -> float:
    """Return the WCAG contrast ratio between
       foreground and background colors."""

    def _normalize_channel(channel: int) -> float:
        return channel / 255

    def _linear_gamma(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        else:
            return (((channel + 0.055) / 1.055) ** 2.4)

    # Normalize to 0-1
    normalize_fg: dict[str, float] = {
        field.name: _normalize_channel(getattr(fg, field.name))
        for field in fields(fg)
        if field.name != 'a'
    }

    normalize_bg: dict[str, float] = {
        field.name: _normalize_channel(getattr(bg, field.name))
        for field in fields(bg)
        if field.name != 'a'
    }

    # Linearized Gamma
    linearized_fg: dict[str, float] = {k: _linear_gamma(v)
                                       for k, v in normalize_fg.items()}
    linearized_bg: dict[str, float] = {k: _linear_gamma(v)
                                       for k, v in normalize_bg.items()}

    # Relative Luminance
    lf = (0.2126 * linearized_fg["r"] +
          0.7152 * linearized_fg["g"] +
          0.0722 * linearized_fg["b"])

    lb = (0.2126 * linearized_bg["r"] +
          0.7152 * linearized_bg["g"] +
          0.0722 * linearized_bg["b"])

    if lf > lb:
        return (lf + 0.05) / (lb + 0.05)
    else:
        return (lb + 0.05) / (lf + 0.05)
