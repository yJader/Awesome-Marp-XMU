#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _run(cmd: List[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(cmd)}")
    if proc.stdout:
        print(proc.stdout.strip())


def _pick_section(sections: List[Dict[str, Any]], keywords: List[str]) -> Dict[str, Any]:
    for sec in sections:
        title = str(sec.get("title", "")).lower()
        if any(k in title for k in keywords):
            return sec
    return sections[0] if sections else {"title": "内容", "bullets": [], "paragraphs": []}


def _top_points(sec: Dict[str, Any], limit: int = 4) -> List[str]:
    bullets = sec.get("bullets", [])
    paras = sec.get("paragraphs", [])
    out: List[str] = []
    for x in bullets + paras:
        s = str(x).strip()
        if not s:
            continue
        out.append(s)
        if len(out) >= limit:
            break
    return out or ["待补充内容"]


def _pick_images(image_hints: List[str]) -> List[str]:
    local = []
    for x in image_hints:
        s = str(x)
        if s.startswith("http://") or s.startswith("https://") or s.startswith("data:"):
            continue
        if any(s.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".pdf", ".eps"]):
            local.append(s)
    unique = []
    seen = set()
    for item in local:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique[:3]


def _resolve_local_image_path(image_ref: str, base_dir: Path) -> Optional[Path]:
    if image_ref.startswith("http://") or image_ref.startswith("https://") or image_ref.startswith("data:"):
        return None
    p = Path(image_ref)
    if not p.is_absolute():
        p = (base_dir / p).resolve()
    if p.exists() and p.is_file():
        return p
    return None


def _get_png_size(path: Path) -> Optional[Tuple[int, int]]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width > 0 and height > 0:
        return width, height
    return None


def _get_gif_size(path: Path) -> Optional[Tuple[int, int]]:
    data = path.read_bytes()
    if len(data) < 10 or data[:3] != b"GIF":
        return None
    width = int.from_bytes(data[6:8], "little")
    height = int.from_bytes(data[8:10], "little")
    if width > 0 and height > 0:
        return width, height
    return None


def _get_jpeg_size(path: Path) -> Optional[Tuple[int, int]]:
    with path.open("rb") as f:
        if f.read(2) != b"\xff\xd8":
            return None
        while True:
            marker_start = f.read(1)
            if not marker_start:
                return None
            while marker_start == b"\xff":
                marker_start = f.read(1)
                if not marker_start:
                    return None
            marker = marker_start[0]
            if marker in {0xD8, 0xD9}:
                continue
            seg_len_raw = f.read(2)
            if len(seg_len_raw) != 2:
                return None
            seg_len = int.from_bytes(seg_len_raw, "big")
            if seg_len < 2:
                return None
            sof_markers = {
                0xC0, 0xC1, 0xC2, 0xC3,
                0xC5, 0xC6, 0xC7,
                0xC9, 0xCA, 0xCB,
                0xCD, 0xCE, 0xCF,
            }
            if marker in sof_markers:
                _ = f.read(1)  # precision
                h = int.from_bytes(f.read(2), "big")
                w = int.from_bytes(f.read(2), "big")
                if w > 0 and h > 0:
                    return w, h
                return None
            f.seek(seg_len - 2, 1)


def _parse_svg_dimension(value: str) -> Optional[float]:
    m = re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)", value)
    if not m:
        return None
    return float(m.group(1))


def _get_svg_size(path: Path) -> Optional[Tuple[int, int]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    head = text[:5000]
    width_m = re.search(r'width\s*=\s*"([^"]+)"', head, re.IGNORECASE)
    height_m = re.search(r'height\s*=\s*"([^"]+)"', head, re.IGNORECASE)
    if width_m and height_m:
        w = _parse_svg_dimension(width_m.group(1))
        h = _parse_svg_dimension(height_m.group(1))
        if w and h and w > 0 and h > 0:
            return int(w), int(h)
    view_m = re.search(r'viewBox\s*=\s*"([^"]+)"', head, re.IGNORECASE)
    if view_m:
        parts = re.split(r"\s+", view_m.group(1).strip())
        if len(parts) == 4:
            try:
                w = float(parts[2])
                h = float(parts[3])
                if w > 0 and h > 0:
                    return int(w), int(h)
            except ValueError:
                return None
    return None


def _probe_image_ratio(image_ref: str, base_dir: Path) -> Optional[float]:
    path = _resolve_local_image_path(image_ref, base_dir)
    if path is None:
        return None
    suffix = path.suffix.lower()
    size = None
    try:
        if suffix == ".png":
            size = _get_png_size(path)
        elif suffix in {".jpg", ".jpeg"}:
            size = _get_jpeg_size(path)
        elif suffix == ".gif":
            size = _get_gif_size(path)
        elif suffix == ".svg":
            size = _get_svg_size(path)
    except OSError:
        return None
    if not size:
        return None
    w, h = size
    if h <= 0:
        return None
    return w / h


def _choose_layout_by_ratio(image_ref: str, base_dir: Path, prefer_pin: bool = False) -> Tuple[str, Optional[float], str]:
    ratio = _probe_image_ratio(image_ref, base_dir)
    if ratio is None:
        return "cols-2-64", None, "ratio unknown -> fallback cols-2-64"
    if ratio >= 1.45:
        return "rows-2", ratio, "wide image"
    if ratio <= 0.85:
        return "cols-2-46", ratio, "tall image"
    if prefer_pin:
        return "pin-3", ratio, "balanced image -> pin-3"
    return "cols-2-64", ratio, "balanced image"


def _render_ratio_adaptive_section(
    title: str,
    points: List[str],
    image_ref: str,
    source_url: str,
    base_dir: Path,
    prefer_pin: bool = False,
) -> List[str]:
    layout_class, ratio, ratio_reason = _choose_layout_by_ratio(image_ref, base_dir, prefer_pin=prefer_pin)
    ratio_text = "unknown" if ratio is None else f"{ratio:.2f}"
    lines: List[str] = ["", "---", "", f"## {title}", "", f"<!-- image_ratio: {ratio_text}; {ratio_reason} -->", f"<!-- _class: {layout_class} -->", ""]

    if layout_class == "rows-2":
        lines.extend([
            "<div class=\"tdiv\">",
            "<div class=\"timg\">",
            "",
            f"![w:90% #c]({image_ref})",
            "",
            "</div>",
            "</div>",
            "<div class=\"bdiv\">",
        ])
        for p in points:
            lines.append(f"- {p}")
        lines.append(f"- 来源：[{source_url}]({source_url})" if source_url else "- 来源：arXiv")
        lines.extend(["", "</div>"])
        return lines

    if layout_class == "pin-3":
        left_points = points[:2] or ["关键要点 A", "关键要点 B"]
        right_points = points[2:4] or ["关键结论与启发", "局限与改进方向"]
        lines.extend([
            "<div class=\"tdiv\">",
            "<div class=\"timg\">",
            "",
            f"![w:82% #c]({image_ref})",
            "",
            "</div>",
            "</div>",
            "<div class=\"ldiv\">",
        ])
        for p in left_points:
            lines.append(f"- {p}")
        lines.extend(["", "</div>", "<div class=\"rdiv\">"])
        for p in right_points:
            lines.append(f"- {p}")
        lines.append(f"- 来源：[{source_url}]({source_url})" if source_url else "- 来源：arXiv")
        lines.extend(["", "</div>"])
        return lines

    # cols-2-64 or cols-2-46
    lines.extend([
        "<div class=\"ldiv\">",
    ])
    for p in points:
        lines.append(f"- {p}")
    lines.append(f"- 来源：[{source_url}]({source_url})" if source_url else "- 来源：arXiv")
    lines.extend([
        "",
        "</div>",
        "<div class=\"rdiv\">",
        "<div class=\"rimg\">",
        "",
        f"![w:95% #c]({image_ref})",
        "",
        "</div>",
        "</div>",
    ])
    return lines


def _build_slides(data: Dict[str, Any], out_md: Path, source_url: str) -> None:
    sections = data.get("sections", [])
    image_hints = data.get("image_hints", [])
    title = str(data.get("title", out_md.stem))
    method_sec = _pick_section(sections, ["method", "approach", "pipeline", "方法", "模型", "流程"])
    result_sec = _pick_section(sections, ["result", "experiment", "evaluation", "结果", "实验", "性能"])
    compare_sec = _pick_section(sections, ["ablation", "baseline", "compare", "对比", "消融"])
    images = _pick_images(image_hints)

    method_img = images[0] if len(images) > 0 else "images/placeholder-method.png"
    result_img = images[1] if len(images) > 1 else "images/placeholder-result.png"
    compare_img = images[2] if len(images) > 2 else "images/placeholder-compare-main.png"

    lines: List[str] = []
    lines.extend([
        "---",
        "marp: true",
        "size: 16:9",
        "theme: am_xmu",
        "paginate: true",
        "headingDivider: [2,3]",
        "math: true",
        "footer: \"\"",
        "---",
        "",
        "<!-- _class: cover_e -->",
        "<!-- _header: \"\" -->",
        "<!-- _footer: \"\" -->",
        "<!-- _paginate: \"\" -->",
        "",
        f"# {title}",
        "",
        "###### arXiv 论文汇报",
        "",
        "---",
        "",
        "<!-- _class: toc_a -->",
        "<!-- _header: \"CONTENTS\" -->",
        "<!-- _footer: \"\" -->",
        "<!-- _paginate: \"\" -->",
        "",
        "- 背景与问题",
        "- 方法与流程",
        "- 关键结果",
        "- 对比与讨论",
        "- 结论与展望",
        "",
        "---",
        "",
        "## 背景与问题",
    ])
    for p in _top_points(_pick_section(sections, ["intro", "background", "motivation", "背景", "引言"])):
        lines.append(f"- {p}")

    lines.extend(
        _render_ratio_adaptive_section(
            "方法与流程",
            _top_points(method_sec),
            method_img,
            source_url,
            out_md.parent,
            prefer_pin=False,
        )
    )
    lines.extend(
        _render_ratio_adaptive_section(
            "关键结果",
            _top_points(result_sec),
            result_img,
            source_url,
            out_md.parent,
            prefer_pin=False,
        )
    )
    compare_points = _top_points(compare_sec, limit=4)
    lines.extend(
        _render_ratio_adaptive_section(
            "对比与讨论",
            compare_points,
            compare_img,
            source_url,
            out_md.parent,
            prefer_pin=True,
        )
    )
    lines.extend([
        "",
        "---",
        "",
        "## 结论与展望",
        "- 工作总结",
        "- 可扩展方向",
        "- 落地建议",
        "",
        "---",
        "",
        "## 参考文献",
    ])
    if source_url:
        lines.append(f"- [1] arXiv: {source_url}")
    for url in data.get("citations", [])[:4]:
        if source_url and url == source_url:
            continue
        lines.append(f"- {url}")
    lines.extend([
        "",
        "---",
        "",
        "<!-- _class: lastpage -->",
        "",
        "###### Q & A",
        "",
        "感谢各位的聆听！",
        "",
    ])
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build initial Marp slides from arXiv link")
    parser.add_argument("arxiv", help="arXiv URL or ID")
    parser.add_argument("--ppt-name", required=True, help="ppt filename, e.g. report.pptx")
    parser.add_argument("--out-md", help="output markdown path")
    parser.add_argument("--out-root", default="workspace/arxiv", help="arXiv workspace root")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    fetch_script = script_dir / "fetch_arxiv_source.py"
    extract_script = script_dir / "extract_content.py"
    collect_script = script_dir / "collect_slide_assets.py"

    with tempfile.TemporaryDirectory(prefix="arxiv-build-") as tmpdir:
        bundle_probe = Path(tmpdir) / "bundle.json"
        _run([
            sys.executable,
            str(fetch_script),
            args.arxiv,
            "--out-root",
            args.out_root,
            "--emit-json",
            str(bundle_probe),
        ])
        bundle = json.loads(bundle_probe.read_text(encoding="utf-8"))

    paper_dir = Path(bundle["paper_dir"]).resolve()
    bundle_path = paper_dir / "arxiv_bundle.json"
    if not bundle_path.exists():
        bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    extract_out = paper_dir / "extract.json"
    _run([sys.executable, str(extract_script), str(bundle_path), "--out", str(extract_out)])

    data = json.loads(extract_out.read_text(encoding="utf-8"))
    source_url = str(bundle.get("source_url", ""))

    default_md_name = f"{Path(args.ppt_name).stem}.md"
    out_md = Path(args.out_md).resolve() if args.out_md else (paper_dir / default_md_name)
    _build_slides(data, out_md, source_url)

    _run([
        sys.executable,
        str(collect_script),
        str(out_md),
        "--ppt-name",
        args.ppt_name,
        "--rewrite-paths",
        "--convert-pdf-to-png",
        "--cleanup-stale-pdf",
    ])
    print(f"[build_from_arxiv] slides: {out_md}")
    print(f"[build_from_arxiv] assets: {out_md.parent / (Path(args.ppt_name).stem + '.assets')}")


if __name__ == "__main__":
    main()
