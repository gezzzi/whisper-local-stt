"""Generate simple tray icons for the app."""
from PIL import Image, ImageDraw


def create_icon(color: str, path: str) -> None:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Microphone shape (simplified)
    # Body
    draw.rounded_rectangle([20, 8, 44, 38], radius=10, fill=color)
    # Stand
    draw.arc([16, 24, 48, 52], start=0, end=180, fill=color, width=3)
    # Base
    draw.line([32, 52, 32, 58], fill=color, width=3)
    draw.line([22, 58, 42, 58], fill=color, width=3)

    img.save(path)
    print(f"Created {path}")


if __name__ == "__main__":
    create_icon("#4A9EFF", "assets/icon.png")
    create_icon("#FF4444", "assets/icon_recording.png")
