#!/usr/bin/env python3
import argparse
import json
import re
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.request import Request, urlopen

FIG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".pdf", ".eps"}
VECTOR_EXTENSIONS = {".pdf", ".eps"}


def _fail(msg: str) -> None:
    print(f"[fetch_arxiv_source] {msg}", file=sys.stderr)
    sys.exit(1)


def _parse_paper_id(value: str) -> str:
    value = value.strip()
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", value)
    if m:
        return m.group(1)
    m = re.search(r"^([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)$", value)
    if m:
        return m.group(1)
    m = re.search(r"arxiv\.org/abs/([a-zA-Z\-]+/[0-9]{7}(?:v\d+)?)", value)
    if m:
        return m.group(1)
    m = re.search(r"^([a-zA-Z\-]+/[0-9]{7}(?:v\d+)?)$", value)
    if m:
        return m.group(1)
    _fail(f"无法解析 arXiv ID: {value}")
    return ""


def _download(url: str, dst: Path, timeout: int) -> None:
    req = Request(url, headers={"User-Agent": "marp-report-deck/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dst.write_bytes(data)


def _extract_archive(archive_path: Path, source_dir: Path) -> str:
    source_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive_path, "r:*") as tf:
            tf.extractall(source_dir)
            return "tar"
    except tarfile.TarError:
        pass

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(source_dir)
            return "zip"
    except zipfile.BadZipFile:
        pass

    _fail(f"无法解压源码包: {archive_path}")
    return ""


def _remove_tex_comments(line: str) -> str:
    # Keep escaped percent like \%
    return re.sub(r"(?<!\\)%.*$", "", line)


def _find_tex_files(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob("*.tex") if p.is_file()])


def _choose_main_tex(tex_files: List[Path]) -> Optional[Path]:
    if not tex_files:
        return None

    scored: List[Tuple[int, int, Path]] = []
    for path in tex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        score = 0
        if r"\documentclass" in content:
            score += 10
        name_lower = path.name.lower()
        if name_lower in {"main.tex", "paper.tex", "ms.tex"}:
            score += 6
        if "arxiv" in name_lower:
            score += 2
        scored.append((score, len(content), path))

    if not scored:
        return tex_files[0]
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return scored[0][2]


def _resolve_include(path_value: str, current_dir: Path, root: Path) -> Optional[Path]:
    name = path_value.strip()
    if not name:
        return None
    candidate = (current_dir / name)
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".tex")
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def _merge_tex(path: Path, root: Path, visited: Set[Path], warnings: List[str]) -> str:
    resolved = path.resolve()
    if resolved in visited:
        warnings.append(f"循环引用已跳过: {resolved}")
        return ""
    visited.add(resolved)

    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        warnings.append(f"读取失败: {path}")
        return ""

    lines = [_remove_tex_comments(x) for x in raw.splitlines()]
    text = "\n".join(lines)

    include_re = re.compile(r"\\(?:input|include)\{([^}]+)\}")

    def repl(match: re.Match[str]) -> str:
        include_name = match.group(1)
        include_file = _resolve_include(include_name, path.parent, root)
        if include_file is None:
            warnings.append(f"未找到 include 文件: {include_name} (from {path.name})")
            return ""
        return _merge_tex(include_file, root, visited, warnings)

    return include_re.sub(repl, text)


def _clean_tex_to_text(tex: str) -> str:
    content = tex
    content = re.sub(r"\\begin\{abstract\}", "\n## Abstract\n", content)
    content = re.sub(r"\\end\{abstract\}", "\n", content)
    content = re.sub(r"\\(?:sub)*section\*?\{([^{}]+)\}", r"\n## \1\n", content)
    content = re.sub(r"\\(?:caption|title)\{([^{}]+)\}", r"\n\1\n", content)

    # Keep command arguments for common forms.
    for _ in range(3):
        content = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", content)
    content = re.sub(r"\\[a-zA-Z@]+\*?(?:\[[^\]]*\])?", " ", content)
    content = content.replace("{", " ").replace("}", " ")
    content = re.sub(r"[ \t]+", " ", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip() + "\n"


def _extract_section_hints(tex: str) -> List[str]:
    hints = re.findall(r"\\(?:sub)*section\*?\{([^{}]+)\}", tex)
    out: List[str] = []
    seen = set()
    for h in hints:
        v = h.strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _collect_figures(source_dir: Path, paper_dir: Path) -> List[Dict[str, object]]:
    figures: List[Dict[str, object]] = []
    for p in sorted(source_dir.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in FIG_EXTENSIONS:
            continue
        rel = p.resolve().relative_to(paper_dir.resolve())
        figures.append({
            "path": str(rel),
            "name": p.name,
            "ext": ext,
            "is_vector": ext in VECTOR_EXTENSIONS,
            "size_bytes": p.stat().st_size,
        })
    return figures


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and unpack arXiv source bundle")
    parser.add_argument("arxiv", help="arXiv URL or ID")
    parser.add_argument("--out-root", default="workspace/arxiv", help="root output directory")
    parser.add_argument("--paper-id", help="override paper id")
    parser.add_argument("--timeout", type=int, default=30, help="download timeout seconds")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing paper dir")
    parser.add_argument("--emit-json", help="custom path for output bundle json")
    args = parser.parse_args()

    paper_id = args.paper_id or _parse_paper_id(args.arxiv)
    paper_dir = Path(args.out_root).resolve() / paper_id
    source_dir = paper_dir / "source"
    archive_path = paper_dir / "source.tar.gz"
    merged_tex_path = paper_dir / "merged.tex"
    clean_text_path = paper_dir / "paper_clean.txt"
    figures_manifest_path = paper_dir / "figures_manifest.json"
    bundle_path = Path(args.emit_json).resolve() if args.emit_json else (paper_dir / "arxiv_bundle.json")
    warnings: List[str] = []

    if paper_dir.exists() and not args.overwrite:
        warnings.append("paper_dir 已存在，重用目录内容（可加 --overwrite 覆盖下载）")
    paper_dir.mkdir(parents=True, exist_ok=True)

    source_url = f"https://arxiv.org/e-print/{paper_id}"
    if args.overwrite or not archive_path.exists():
        _download(source_url, archive_path, args.timeout)

    archive_type = _extract_archive(archive_path, source_dir)
    tex_files = _find_tex_files(source_dir)
    main_tex = _choose_main_tex(tex_files)
    section_hints: List[str] = []

    if main_tex is None:
        warnings.append("未找到任何 tex 文件")
        merged_tex_path.write_text("", encoding="utf-8")
        clean_text_path.write_text("", encoding="utf-8")
    else:
        merged = _merge_tex(main_tex, source_dir, set(), warnings)
        merged_tex_path.write_text(merged, encoding="utf-8")
        clean_text = _clean_tex_to_text(merged)
        clean_text_path.write_text(clean_text, encoding="utf-8")
        section_hints = _extract_section_hints(merged)

    figures = _collect_figures(source_dir, paper_dir)
    figures_manifest_path.write_text(json.dumps(figures, ensure_ascii=False, indent=2), encoding="utf-8")

    bundle = {
        "paper_id": paper_id,
        "source_url": source_url,
        "paper_dir": str(paper_dir),
        "archive_path": str(archive_path),
        "source_dir": str(source_dir),
        "archive_type": archive_type,
        "main_tex_path": str(main_tex) if main_tex else None,
        "merged_tex_path": str(merged_tex_path),
        "clean_text_path": str(clean_text_path),
        "figures_manifest_path": str(figures_manifest_path),
        "figures": figures,
        "sections_hint": section_hints,
        "warnings": warnings,
    }
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[fetch_arxiv_source] paper_dir: {paper_dir}")
    print(f"[fetch_arxiv_source] bundle: {bundle_path}")
    print(f"[fetch_arxiv_source] figures: {len(figures)}")
    for w in warnings:
        print(f"[fetch_arxiv_source] warning: {w}")


if __name__ == "__main__":
    main()
