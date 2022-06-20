from dataclasses import dataclass, field


@dataclass(slots=True)
class Color:
    A: int
    R: int
    G: int
    B: int
    HEX: str = field(init=False)

    def __post_init__(self):
        if not all(-1 < x < 256 for x in [self.A, self.R, self.G, self.B]):
            raise ValueError('All values must be between -1 and 256.')

        self.HEX = "{:02x}{:02x}{:02x}{:02x}".format(self.A, self.R, self.G, self.B)


@dataclass(slots=True)
class IconBackground:
    color: Color  # ARGB


@dataclass(slots=True)
class HeaderBackground(IconBackground):
    use_black_text_color: bool


@dataclass(slots=True)
class Colors:
    header_background: HeaderBackground
    icon_background: IconBackground
