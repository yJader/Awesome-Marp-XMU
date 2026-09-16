#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HTML_IMAGE_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)


def _is_remote(path_text: str) -> bool:
    lower = path_text.lower()
    return lower.startswith("http://") or lower.startswith("https://") or lower.startswith("data:")


def _normalize_md_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target


def _collect_refs(md_text: str) -> List[str]:
    refs: List[str] = []
    refs.extend(MD_IMAGE_RE.findall(md_text))
    refs.extend(HTML_IMAGE_RE.findall(md_text))
    return [_normalize_md_target(x) for x in refs if _normalize_md_target(x)]


def _unique_destination(dst_dir: Path, filename: str) -> Path:
    candidate = dst_dir / filename
    if not candidate.exists():
        return candidate
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    index = 2
    while True:
        alt = dst_dir / f"{stem}-{index}{suffix}"
        if not alt.exists():
            return alt
        index += 1


def _convert_pdf_to_png(src_pdf: Path, dst_png: Path, dpi: int) -> Optional[str]:
    # Prefer pdftoppm for single-page rasterization from vector figures.
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        cmd = [
            pdftoppm,
            "-singlefile",
            "-f",
            "1",
            "-l",
            "1",
            "-r",
            str(dpi),
            "-png",
            str(src_pdf),
            str(dst_png.with_suffix("")),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and dst_png.exists():
            return None
        return (proc.stderr or proc.stdout or "pdftoppm failed").strip()

    gs = shutil.which("gs")
    if gs:
        cmd = [
            gs,
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pngalpha",
            f"-r{dpi}",
            "-dFirstPage=1",
            "-dLastPage=1",
            f"-sOutputFile={dst_png}",
            str(src_pdf),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and dst_png.exists():
            return None
        return (proc.stderr or proc.stdout or "gs failed").strip()

    return "no converter found (need pdftoppm or gs)"


def _copy_assets(
    md_path: Path,
    refs: List[str],
    assets_dir: Path,
    convert_pdf_to_png: bool,
    pdf_dpi: int,
) -> Tuple[Dict[str, str], List[str], int]:
    mapping: Dict[str, str] = {}
    warnings: List[str] = []
    copied_src: Dict[Path, Path] = {}
    converted_pdf: Dict[Path, Path] = {}
    converted_count = 0
    assets_dir.mkdir(parents=True, exist_ok=True)

    for ref in refs:
        if _is_remote(ref):
            continue
        if ref in mapping:
            continue

        src = (md_path.parent / ref).resolve()
        if not src.exists() or not src.is_file():
            warnings.append(f"missing: {ref}")
            continue

        if src in copied_src:
            dst = copied_src[src]
        else:
            if convert_pdf_to_png and src.suffix.lower() == ".pdf":
                png_name = f"{src.stem}.png"
                dst = _unique_destination(assets_dir, png_name)
                if src in converted_pdf:
                    dst = converted_pdf[src]
                else:
                    err = _convert_pdf_to_png(src, dst, pdf_dpi)
                    if err:
                        warnings.append(f"pdf->png failed ({ref}): {err}; fallback copy pdf")
                        dst = _unique_destination(assets_dir, src.name)
                        shutil.copy2(src, dst)
                        copied_src[src] = dst
                    else:
                        converted_pdf[src] = dst
                        converted_count += 1
            else:
                dst = _unique_destination(assets_dir, src.name)
                shutil.copy2(src, dst)
                copied_src[src] = dst

        mapping[ref] = dst.name

    return mapping, warnings, converted_count


def _rewrite_markdown(md_text: str, mapping: Dict[str, str], assets_dir_name: str) -> str:
    def repl_md(match: re.Match[str]) -> str:
        original = _normalize_md_target(match.group(1))
        if original not in mapping:
            return match.group(0)
        new_target = f"{assets_dir_name}/{mapping[original]}"
        return match.group(0).replace(match.group(1), new_target)

    def repl_html(match: re.Match[str]) -> str:
        original = _normalize_md_target(match.group(1))
        if original not in mapping:
            return match.group(0)
        new_target = f"{assets_dir_name}/{mapping[original]}"
        return match.group(0).replace(match.group(1), new_target)

    rewritten = MD_IMAGE_RE.sub(repl_md, md_text)
    rewritten = HTML_IMAGE_RE.sub(repl_html, rewritten)
    return rewritten


def _cleanup_stale_pdfs(assets_dir: Path, active_filenames: set[str]) -> int:
    removed = 0
    for pdf in assets_dir.glob("*.pdf"):
        if pdf.name in active_filenames:
            continue
        pdf.unlink()
        removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy slide images referenced in Markdown to [ppt_name].assets"
    )
    parser.add_argument("markdown", help="path to markdown slide file")
    parser.add_argument("--ppt-name", help="ppt filename, e.g. report.pptx")
    parser.add_argument("--assets-dir", help="override assets output directory")
    parser.add_argument(
        "--rewrite-paths",
        action="store_true",
        help="rewrite markdown image paths to [assets_dir]/<filename>",
    )
    parser.add_argument(
        "--convert-pdf-to-png",
        action="store_true",
        help="convert local .pdf image refs to .png in assets directory",
    )
    parser.add_argument(
        "--pdf-dpi",
        type=int,
        default=220,
        help="DPI used when converting PDF to PNG (default: 220)",
    )
    parser.add_argument(
        "--cleanup-stale-pdf",
        action="store_true",
        help="remove stale .pdf files in assets that are not referenced by current markdown",
    )
    args = parser.parse_args()

    md_path = Path(args.markdown).resolve()
    if not md_path.exists():
        print(f"[collect_slide_assets] markdown not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    refs = _collect_refs(md_text)

    if args.assets_dir:
        assets_dir = Path(args.assets_dir).resolve()
    else:
        ppt_stem = Path(args.ppt_name).stem if args.ppt_name else md_path.stem
        assets_dir = md_path.parent / f"{ppt_stem}.assets"
    assets_dir_name = assets_dir.name

    mapping, warnings, converted_count = _copy_assets(
        md_path, refs, assets_dir, args.convert_pdf_to_png, args.pdf_dpi
    )
    copied_count = len(mapping)
    cleaned_pdf_count = 0

    if args.rewrite_paths and mapping:
        rewritten = _rewrite_markdown(md_text, mapping, assets_dir_name)
        md_path.write_text(rewritten, encoding="utf-8")
    if args.cleanup_stale_pdf and args.convert_pdf_to_png:
        cleaned_pdf_count = _cleanup_stale_pdfs(assets_dir, set(mapping.values()))

    print(f"[collect_slide_assets] assets_dir: {assets_dir}")
    print(f"[collect_slide_assets] referenced: {len(refs)}")
    print(f"[collect_slide_assets] copied: {copied_count}")
    if args.convert_pdf_to_png:
        print(f"[collect_slide_assets] converted_pdf: {converted_count}")
    if args.cleanup_stale_pdf and args.convert_pdf_to_png:
        print(f"[collect_slide_assets] cleaned_stale_pdf: {cleaned_pdf_count}")
    if args.rewrite_paths:
        print("[collect_slide_assets] markdown paths rewritten")
    for w in warnings:
        print(f"[collect_slide_assets] warning: {w}")


if __name__ == "__main__":
    main()
