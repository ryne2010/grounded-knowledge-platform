from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import settings


@dataclass(frozen=True)
class PdfTextResult:
    text: str
    used_ocr_pages: int


def extract_text_from_pdf(path: str | Path) -> PdfTextResult:
    """Extract text from a PDF.

    Strategy:
      1) Try native text extraction per-page via PyMuPDF.
      2) If a page has very little text and OCR is enabled, OCR that page with Tesseract.

    Everything stays local and open source.
    """

    path = Path(path)
    try:
        import fitz  # type: ignore[import-untyped]  # PyMuPDF
    except Exception as e:
        raise RuntimeError("PDF support requires `PyMuPDF` (package: pymupdf).") from e

    used_ocr = 0
    texts: list[str] = []

    with fitz.open(str(path)) as doc:
        for _, page in enumerate(doc):
            page_text = (page.get_text("text") or "").strip()

            # If extracted text is very small, the page is likely scanned.
            if settings.ocr_enabled and len(page_text) < settings.ocr_min_chars:
                if used_ocr < settings.ocr_max_pages:
                    ocr_text = _ocr_page(page)
                    if ocr_text.strip():
                        page_text = ocr_text.strip()
                        used_ocr += 1

            if page_text:
                texts.append(page_text)

    return PdfTextResult(text="\n\n".join(texts), used_ocr_pages=used_ocr)


def _ocr_page(page) -> str:
    """OCR a PyMuPDF page using Tesseract (via pytesseract)."""
    try:
        import pytesseract  # type: ignore[import-untyped]
        from PIL import Image
    except Exception as e:
        raise RuntimeError(
            "OCR requires `pytesseract` and `Pillow`. Install dependencies and ensure `tesseract-ocr` is available."
        ) from e

    pix = page.get_pixmap(dpi=int(settings.ocr_dpi))
    mode = "RGB" if pix.alpha == 0 else "RGBA"
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    if mode == "RGBA":
        img = img.convert("RGB")
    return pytesseract.image_to_string(img, lang=settings.ocr_lang)
