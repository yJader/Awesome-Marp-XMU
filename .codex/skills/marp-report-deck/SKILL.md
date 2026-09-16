---
name: marp-report-deck
description: "使用本技能在需要将论文/报告/PPT/Markdown/笔记整理为 Marp 汇报幻灯片时，包括从文件提取内容、或从 arXiv 链接下载 TeX 源码并提取正文与原图、生成汇报结构、套用 am_xmu 主题与 cover_e 封面、输出含内联引用与参考文献页的 Markdown 幻灯片。"
---

# Marp 汇报幻灯片生成

## 目标

- 将输入资料整理为 10–12 页的中文汇报型 Marp 幻灯片。
- 默认使用 `am_xmu` 主题与 `cover_e` 封面样式。
- 输出包含内联引用与参考文献页。
- 对需要配图的页面，默认使用分栏布局并预留图片位置。

## 输入与输出

- 输入：`arXiv 链接/ID` / `.pdf` / `.pptx` / `.md` / 纯文本（用户粘贴）。
- 输出：Marp Markdown（可直接渲染成幻灯片）。

## 快速流程

1. 收集资料与元信息：标题、作者、时间、汇报场景（答辩/组会/汇报）。
2. 如果输入是文件，运行提取脚本：
   - `python3 .codex/skills/marp-report-deck/scripts/extract_content.py <input-path> --out /tmp/extract.json`
   - arXiv 输入先运行：
   - `python3 .codex/skills/marp-report-deck/scripts/fetch_arxiv_source.py <arxiv_url_or_id> --out-root workspace/arxiv`
   - 再运行：
   - `python3 .codex/skills/marp-report-deck/scripts/extract_content.py workspace/arxiv/<paper_id>/arxiv_bundle.json --out /tmp/extract.json`
3. 依据提取结果中的 `sections` / `image_hints` / `layout_hints` 生成结构化大纲。
4. 为每一页选择布局 class（默认使用场景自适应规则）。
5. 套用模板生成 10–12 页 Marp 幻灯片，并为图片页添加占位。
6. 内联标注关键来源，最后添加参考文献页。
7. 在导出前复制已使用图片到 `ppt文件名.assets`，将 PDF 图片转 PNG（Marp 兼容），并清理陈旧 PDF：
   - `python3 .codex/skills/marp-report-deck/scripts/collect_slide_assets.py <slides.md> --ppt-name <导出文件名.pptx> --rewrite-paths --convert-pdf-to-png --cleanup-stale-pdf`

## arXiv 一键流程

- 一键命令（推荐）：
  - `python3 .codex/skills/marp-report-deck/scripts/build_from_arxiv.py <arxiv_url_or_id> --ppt-name <导出文件名.pptx>`
- 一键流程会执行：
  - 下载与解压源码
  - 提取正文与原图线索
  - 生成 `<ppt文件名>.md` 初稿（与 `.assets` 同名 stem）
  - 复制已使用图片到 `ppt文件名.assets`
  - 自动将 `.pdf` 图片转为 `.png` 并改写 Markdown 路径
  - 清理 `.assets` 中未被当前 Markdown 引用的陈旧 `.pdf`

## 结构与页数（默认）

- 封面（`cover_e`）
- 目录/议程
- 背景与问题
- 方法/模型/流程
- 关键结果（2–3 页）
- 讨论与局限
- 结论与展望
- 参考文献
- Q&A/致谢

## 图片与分栏规范

- 图片页必须使用分栏 class，不要在单栏里堆图和大段文字。
- 场景自适应布局（默认）：
  - 方法/流程/架构页：`cols-2-64`（左文右图）
  - 结果/实验指标页：`rows-2`（上图下结论）
  - 对比/消融页：`pin-3`（主图 + 两个对比块）
- 比例自适应布局（优先级更高）：
  - 长宽比 `>= 1.45`：优先 `rows-2`（宽图）
  - 长宽比 `<= 0.85`：优先 `cols-2-46`（高图）
  - 其余比例：优先 `cols-2-64`（均衡图）
  - 对比页在均衡比例下可优先 `pin-3`
- 图片占位写法（示例）：
  - `![w:95% #c](images/placeholder-method.png)`
  - `![w:90% #c](images/placeholder-result.png)`
- 分栏容器命名：
  - 两列：`ldiv` / `rdiv`，图片容器 `limg` / `rimg`
  - 两行：`tdiv` / `bdiv`，图片容器 `timg` / `bimg`
  - 品字：`tdiv` + `ldiv` + `rdiv`，配套 `timg` / `limg` / `rimg`
- 图片路径与命名约束：
  - 默认放在 `images/`
  - 文件名建议 `topic-section-index.ext`，例如 `diffusion-method-01.png`
- 每个图片页至少保留一行图注或一句解释；除 `pin-3` 外每页仅放 1 张主图。
- 导出规范：将当前 Markdown 中实际引用的本地图片复制到 `ppt文件名.assets` 目录，确保可打包与迁移。

## 模板与样式

- 参考模板文件：
  - `themes/am_xmu.scss`
  - `themes/am_template.scss`
  - `examples/AwesomeMarp_xmu.md`
- 使用 `assets/slide_skeleton.md` 作为骨架，按需扩充。
- 每页只放一个核心观点，建议 3–6 条要点，不写大段正文。

## 提取脚本说明

- 脚本：`scripts/extract_content.py`
- 依赖：`pypdf`（PDF）、`python-pptx`（PPTX）
- 若依赖缺失，脚本会提示安装方式。
- 关键输出字段：
  - `sections`：结构化文本内容
  - `image_hints`：图片线索（图号、图片路径、图相关语句）
  - `layout_hints`：每个 section 的建议布局 class
- 支持输入类型：
  - `.md` / `.pdf` / `.pptx`
  - arXiv bundle `.json`（由 `fetch_arxiv_source.py` 产出）

## arXiv 脚本说明

- 脚本：`scripts/fetch_arxiv_source.py`
- 作用：根据 arXiv 链接下载 TeX 源码，解压后提取正文和原图清单。
- 默认产物目录：`workspace/arxiv/<paper_id>`
- 关键产物：
  - `arxiv_bundle.json`
  - `paper_clean.txt`
  - `figures_manifest.json`
- 默认策略：
  - 保留源码包、解压目录、正文文本、原图清单
  - `pdf/eps` 矢量图仅索引，不自动转换

## 一键构建脚本说明

- 脚本：`scripts/build_from_arxiv.py`
- 作用：串联 arXiv 下载、内容提取、初稿生成、`.assets` 收集。
- 图片容器选择：根据配图长宽比自动选择分栏容器，并写入页面注释（`image_ratio` + 选择原因）。
- 默认命名：`<ppt文件名>.md` 与 `<ppt文件名>.assets` 保持一致。
- 常用命令：
  - `python3 .codex/skills/marp-report-deck/scripts/build_from_arxiv.py <arxiv_url_or_id> --ppt-name report.pptx`

## 资源收集脚本说明

- 脚本：`scripts/collect_slide_assets.py`
- 作用：扫描 Markdown 中 `![]()` 与 `<img src=\"...\">` 的本地图片路径并复制到 `ppt文件名.assets`。
- 默认行为：
  - 目标目录：`<slides.md同级>/<ppt文件名>.assets`
  - 跳过远程图片（`http/https/data`）
  - 文件重名自动加序号避免覆盖
- 常用参数：
  - `--ppt-name`：指定 PPT 文件名
  - `--assets-dir`：指定输出目录
  - `--rewrite-paths`：将 Markdown 图片路径改写为 `.assets` 相对路径
  - `--convert-pdf-to-png`：将本地 `.pdf` 图片转换为 `.png`（默认转换第一页）
  - `--pdf-dpi`：PDF 转 PNG 分辨率（默认 220）
  - `--cleanup-stale-pdf`：转换后清理 `.assets` 中未被当前文档使用的 `.pdf`

## 引用规范

- 重要结论或数据在页面要点中以内联形式标注来源。
- 末尾添加“参考文献/参考资料”页，列出完整来源链接或文献信息。

## 质量检查

- 结构完整、层次清晰、页数在 10–12 页附近。
- 关键结论可追溯到引用来源。
- 语言简洁，避免重复与口语化过度。
