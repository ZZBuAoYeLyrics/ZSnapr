
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
ICONS_DIR = BASE_DIR / "icons"
DEFAULT_TTF = ICONS_DIR / "MaterialSymbolsOutlined-VariableFont_FILL,GRAD,opsz,wght.ttf"
DEFAULT_CODEPOINTS = ICONS_DIR / "MaterialSymbolsOutlined[FILL,GRAD,opsz,wght].codepoints"


@dataclass(frozen=True)
class IconVariations:
    """Variable font axis configuration for Material Symbols."""
    fill: float = 0.0          # 0..1
    weight: int = 400          # 100..700
    grade: float = 0.0         # -25..200
    optical_size: int = 48     # 20, 24, 40, 48


@dataclass(frozen=True)
class RenderConfig:
    """Rendering configuration."""
    size: int = 24
    color: Tuple[int, int, int, int] = (0, 0, 0, 255)            # RGBA
    background: Optional[Tuple[int, int, int, int]] = None       # None => transparent
    padding: int = 0
    format: str = "PNG"                                          # PNG, JPEG, ...


class MaterialSymbolsTTFManager:
    """Local TTF icon manager for Material Symbols Outlined variable font."""



    def __init__(
        self,
        ttf_path: Optional[str] = None,
        codepoints_file: Optional[str] = None,
        cache_enabled: bool = True,
    ):
        """Initialize manager and try to load codepoints from file."""
        # Resolve font path
        self.ttf_path = Path(ttf_path) if ttf_path else DEFAULT_TTF
        if not self.ttf_path.exists():
            logger.warning(f"Font file not found: {self.ttf_path}")

        self.cache_enabled = cache_enabled
        self._font_cache: Dict[Tuple, ImageFont.FreeTypeFont] = {}
        self._image_cache: Dict[str, Image.Image] = {}

        # Use codepoints file only (ignore built-in fallback map)
        self.ICON_CODEPOINTS = {}

        # Load extra codepoints if available; default to local file if not given
        cp_path = Path(codepoints_file) if codepoints_file else DEFAULT_CODEPOINTS
        if cp_path.exists():
            self._load_codepoints(cp_path)
        else:
            logger.warning(f"Codepoints file not found: {cp_path}")

        logger.info(f"Manager ready. Font: {self.ttf_path.name if self.ttf_path.exists() else 'MISSING'}, "
                    f"icons: {len(self.ICON_CODEPOINTS)}")

    def _load_codepoints(self, filepath: Path) -> None:
        """Load codepoints mapping. Format: 'icon_name HEXCODEPOINT' per line."""
        loaded = 0
        try:
            with filepath.open("r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    parts = s.split()
                    if len(parts) >= 2:
                        name = parts[0].lower().replace("-", "_")
                        try:
                            codepoint = int(parts[1], 16)
                            self.ICON_CODEPOINTS[name] = codepoint
                            loaded += 1
                        except ValueError:
                            continue
            logger.info(f"Loaded {loaded} codepoints from {filepath.name}")
        except Exception as e:
            logger.error(f"Failed to load codepoints: {e}")

    def get_font(self, size: int = 24, variations: Optional[IconVariations] = None) -> ImageFont.FreeTypeFont:
        """Return a PIL FreeTypeFont configured with variable axes if supported."""
        if not self.ttf_path.exists():
            raise FileNotFoundError(f"Font file not found: {self.ttf_path}")

        variations = variations or IconVariations()
        cache_key = (size, variations.fill, variations.weight, variations.grade, variations.optical_size)
        if self.cache_enabled and cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font = ImageFont.truetype(str(self.ttf_path), size=size)
        # Set variable font axes if available in this PIL build
        try:
            font.set_variation_by_axes([
                variations.fill,          # FILL
                variations.grade,         # GRAD
                variations.optical_size,  # opsz
                variations.weight,        # wght
            ])
        except Exception:
            logger.debug("Variable font axes not applied (unsupported or failed).")

        if self.cache_enabled:
            self._font_cache[cache_key] = font
        return font

    def get_icon_unicode(self, icon_name: str) -> Optional[int]:
        """Return codepoint for icon name or None if not found."""
        normalized = icon_name.lower().replace("-", "_")
        return self.ICON_CODEPOINTS.get(normalized)

    def render_icon(
        self,
        icon_name: str,
        config: Optional[RenderConfig] = None,
        variations: Optional[IconVariations] = None,
    ) -> Image.Image:
        """Render an icon to a PIL Image."""
        config = config or RenderConfig()
        variations = variations or IconVariations()

        codepoint = self.get_icon_unicode(icon_name)
        if codepoint is None:
            raise ValueError(f"Unknown icon name: {icon_name}")

        cache_key = f"{icon_name}|{config.size}|{config.color}|{config.background}|{config.padding}|{variations}"
        if self.cache_enabled and cache_key in self._image_cache:
            return self._image_cache[cache_key].copy()

        font = self.get_font(config.size, variations)

        img_size = config.size + (config.padding * 2)
        bg = config.background if config.background else (255, 255, 255, 0)
        image = Image.new("RGBA", (img_size, img_size), bg)
        draw = ImageDraw.Draw(image)

        char = chr(codepoint)
        bbox = draw.textbbox((0, 0), char, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (img_size - text_w) // 2 - bbox[0]
        y = (img_size - text_h) // 2 - bbox[1]

        draw.text((x, y), char, fill=config.color, font=font)

        if self.cache_enabled:
            self._image_cache[cache_key] = image.copy()
        return image

    def save_icon(
        self,
        icon_name: str,
        output_path: str,
        config: Optional[RenderConfig] = None,
        variations: Optional[IconVariations] = None,
    ) -> None:
        """Render and save icon image."""
        img = self.render_icon(icon_name, config, variations)
        fmt = (config.format if config else "PNG") or "PNG"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, fmt)
        logger.info(f"Saved: {output_path}")

    def batch_render(
        self,
        icon_names: List[str],
        output_dir: str,
        config: Optional[RenderConfig] = None,
        variations: Optional[IconVariations] = None,
    ) -> None:
        """Batch render icons."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name in icon_names:
            try:
                filename = f"{name}_{config.size if config else 24}.png"
                self.save_icon(name, str(out / filename), config, variations)
            except Exception as e:
                logger.error(f"Skip {name}: {e}")

    def list_available_icons(self) -> List[str]:
        """Return all available icon names sorted."""
        return sorted(self.ICON_CODEPOINTS.keys())

    def search_icons(self, keyword: str) -> List[str]:
        """Return icon names containing keyword."""
        kw = keyword.lower()
        return [n for n in self.ICON_CODEPOINTS.keys() if kw in n]

    def get_icon_as_text(self, icon_name: str) -> str:
        """Return the icon as a single-character string."""
        cp = self.get_icon_unicode(icon_name)
        if cp is None:
            raise ValueError(f"Unknown icon: {icon_name}")
        return chr(cp)

    def export_html_demo(self, output_file: str = "icons_demo.html", limit: int = 100) -> None:
        """Export a basic HTML page that shows icons using the TTF as webfont."""
        if not self.ttf_path.exists():
            raise FileNotFoundError(f"Font file not found: {self.ttf_path}")

        # Copy hint: this HTML assumes the TTF file is in the same directory as the HTML output.
        # Place the TTF next to the HTML or adjust src url accordingly.
        font_url = self.ttf_path.name
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '  <meta charset="UTF-8" />',
            "  <title>Material Symbols Icons Demo</title>",
            "  <style>",
            "    @font-face {",
            "      font-family: 'Material Symbols Outlined';",
            f"      src: url('{font_url}') format('truetype');",
            "    }",
            "    .material-icons {",
            "      font-family: 'Material Symbols Outlined';",
            "      font-weight: normal;",
            "      font-style: normal;",
            "      font-size: 24px;",
            "      display: inline-block;",
            "      line-height: 1;",
            "      text-transform: none;",
            "      letter-spacing: normal;",
            "      word-wrap: normal;",
            "      white-space: nowrap;",
            "      direction: ltr;",
            "      -webkit-font-smoothing: antialiased;",
            "      text-rendering: optimizeLegibility;",
            "      -moz-osx-font-smoothing: grayscale;",
            "      font-feature-settings: 'liga';",
            "    }",
            "    .grid {",
            "      display: grid;",
            "      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));",
            "      gap: 16px; padding: 16px;",
            "    }",
            "    .item { border: 1px solid #e0e0e0; border-radius: 8px; text-align:center; padding:12px; }",
            "    .glyph { font-size: 40px; margin: 6px; }",
            "    .name { font-size: 12px; color: #666; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>Material Symbols Icons</h1>",
            '  <div class="grid">',
        ]

        count = 0
        for name in self.list_available_icons():
            if limit and count >= limit:
                break
            try:
                char = self.get_icon_as_text(name)
                html_parts.append('    <div class="item">')
                html_parts.append(f'      <div class="material-icons glyph">{char}</div>')
                html_parts.append(f'      <div class="name">{name}</div>')
                html_parts.append("    </div>")
                count += 1
            except Exception:
                continue

        html_parts += [
            "  </div>",
            "</body>",
            "</html>",
        ]

        Path(output_file).write_text("\n".join(html_parts), encoding="utf-8")
        logger.info(f"HTML demo saved: {output_file}")


if __name__ == "__main__":
    # Quick smoke test example (paths auto-resolve to local icons directory)
    manager = MaterialSymbolsTTFManager()
    try:
        cfg = RenderConfig(size=48, color=(33, 150, 243, 255))
        var = IconVariations(fill=1.0, weight=500)
        (BASE_DIR / "preview").mkdir(exist_ok=True)
        manager.save_icon("home", str(BASE_DIR / "preview" / "home.png"), cfg)
        manager.save_icon("favorite", str(BASE_DIR / "preview" / "favorite_filled.png"), cfg, var)
        manager.batch_render(["search", "settings", "notifications", "person", "menu"], str(BASE_DIR / "preview"), cfg)
        logger.info("Preview icons rendered in 'core/font_manager/preview'")
    except Exception as e:
        logger.error(f"Smoke test failed: {e}")