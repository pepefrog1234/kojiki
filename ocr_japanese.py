"""Command-line tool to OCR Japanese text from images using OpenAI's Responses API."""
from __future__ import annotations

import argparse
import base64
import mimetypes
import os
from glob import glob
from pathlib import Path
from typing import Iterable

from openai import OpenAI


PROMPT = (
    "You are an OCR assistant. Transcribe all Japanese text from the image. "
    "Preserve the reading order as much as possible and keep the output in Markdown."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe Japanese text from images via the OpenAI API and save to Markdown files.",
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Paths to image files to transcribe.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./ocr_output",
        help=(
            "Directory where Markdown files should be written. "
            "If omitted, files are saved in ./ocr_output."
        ),
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model to use for OCR (default: gpt-4.1-mini).",
    )
    return parser.parse_args()


def ensure_output_dir(path: str | os.PathLike[str]) -> Path:
    output_path = Path(path).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def response_to_text(response) -> str:
    """Extract plain text from a Responses API call."""
    if hasattr(response, "output_text"):
        return response.output_text

    # Fallback in case output_text is unavailable (older client versions).
    text_parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        content = getattr(item, "content", []) or []
        for block in content:
            if getattr(block, "type", None) == "output_text":
                text_parts.append(getattr(block, "text", ""))
    return "\n".join(text_parts)


def save_markdown(text: str, target_path: Path) -> None:
    target_path.write_text(text, encoding="utf-8")


def guess_output_filename(image_path: Path) -> str:
    return f"{image_path.stem}.md"


def call_ocr(client: OpenAI, model: str, image_path: Path) -> str:
    image_bytes = image_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    mime_type, _ = mimetypes.guess_type(image_path.name)
    image_payload = {
        "data": image_b64,
        "mime_type": mime_type or "application/octet-stream",
    }

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    {"type": "input_image", "image": image_payload},
                ],
            }
        ],
    )
    return response_to_text(response)


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def natural_sort_key(path: Path) -> tuple:
    """Return a key that sorts filenames in human order (e.g., 1, 2, 10)."""
    parts: list[tuple[int, int | str]] = []
    token = ""
    for char in path.stem:
        if char.isdigit():
            token += char
        else:
            if token:
                parts.append((0, int(token)))
                token = ""
            parts.append((1, char.lower()))
    if token:
        parts.append((0, int(token)))
    return tuple(parts)


def iter_images_in_directory(directory: Path) -> list[Path]:
    return sorted(
        [p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file()],
        key=natural_sort_key,
    )


def process_single_image(client: OpenAI, model: str, image_path: Path, output_dir: Path) -> None:
    print(f"Processing {image_path} ...")
    text = call_ocr(client, model, image_path)
    output_file = output_dir / guess_output_filename(image_path)
    save_markdown(text, output_file)
    print(f"Saved Markdown to {output_file}")


def process_image_directory(client: OpenAI, model: str, directory: Path, output_dir: Path) -> None:
    images = iter_images_in_directory(directory)
    if not images:
        raise FileNotFoundError(f"No images found in directory: {directory}")

    combined_parts: list[str] = []
    for image in images:
        print(f"Processing {image} ...")
        text = call_ocr(client, model, image)
        combined_parts.append(f"## {image.stem}\n\n{text}")

    combined_output = "\n\n".join(part.strip() for part in combined_parts if part.strip())
    output_file = output_dir / f"{directory.name}.md"
    save_markdown(combined_output, output_file)
    print(f"Saved combined Markdown to {output_file}")


def expand_inputs(image_paths: Iterable[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw_path in image_paths:
        if any(char in raw_path for char in "*?[]"):
            matches = sorted(
                (Path(match) for match in glob(raw_path, recursive=True)),
                key=lambda p: str(p).lower(),
            )
            if not matches:
                raise FileNotFoundError(f"No files matched the pattern: {raw_path}")
            expanded.extend(matches)
            continue

        expanded.append(Path(raw_path))

    if not expanded:
        raise FileNotFoundError("No input images or directories were provided.")

    return expanded


def process_images(image_paths: Iterable[Path], output_dir: Path, model: str) -> None:
    client = OpenAI()

    for path in image_paths:
        if path.is_dir():
            process_image_directory(client, model, path, output_dir)
            continue

        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")

        process_single_image(client, model, path, output_dir)


def main() -> None:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    inputs = expand_inputs(args.images)
    process_images(inputs, output_dir, args.model)


if __name__ == "__main__":
    main()
