---
marp: true
theme: am_xmu
size: 16:9
header: "Marp主题使用与编辑"
# title: "Marp 主题使用"
footer: "\ *亦瑾* &nbsp; *2025年09月30日*"
headingDivider: [2] # 自动根据标题级别添加分割线
---

<!-- markdownlint-disable MD029 MD001 MD033 -->
<!-- _class: cover_e -->
<!-- _header: "![](./themes/assets/xmu_logo.svg)" -->
<!-- _footer: "![](./themes/assets/xmu_logo_name.svg)" -->

# Marp主题使用与编辑

###### “用法简单、功能全面的个性化 PPT 模板”

在配置和修改Awesome Marp主题时, 碰到了一些坑点, 记录一下
其实这个markdown也是用Marp写的, 可以预览试试XD

## DIY theme

### 如何DIY你学校的模板

#### Step1 查找你学校的资源

1. 校徽: 可以在[Figma-中国大学矢量校徽合集](https://www.figma.com/community/file/916515339708288305)导出svg/png
2. 主题色:
   - 同样在Figma中, 查看校徽对应颜色
   - 或者查看你的学校是否有视觉设计标准, 如厦门大学可以检索到: [厦门大学视觉识别系统-厦门大学办公室](https://office.xmu.edu.cn/info/1009/1058.htm), [关于举办厦门大学百年校庆版新生录取通知书设计大赛的通知-厦门大学招生网](https://zs.xmu.edu.cn/info/1041/1917.htm)

---

#### Step2 修改模板

可以参考[am_xmu.scss](themes/am_xmu.scss)中的修改, 在其中加上了注释, 即便不熟悉css的同学应该也能完成 ~~(比如我)~~

主要逻辑:

1. 定义学校颜色变量, 其中不同透明度(白底)的RGB值计算可以直接交给LLM完成
2. 在需要编辑的颜色处调用, 如`--color-coverbg: var(--color-xmu-blue-100);`

---

#### Step3 添加图片资源

在[themes/assets](./themes/assets)文件夹中, 我放置了我需要的校徽文件

主要使用位置为

1. 本文件封面

```markdown
<!-- _class: cover_e -->
<!-- _header: "![](./themes/assets/xmu_logo.svg)" -->
<!-- _footer: "![](./themes/assets/xmu_logo_name.svg)" -->
```

2. 在 Markdown 的 YAML 头部设置全局页眉，模板将普通页的文字放在左上角、校徽放在右上角：

```yaml
header: "章节标题 ![](./themes/assets/xmu_logo_name.svg)"
```

只写图片时只显示校徽，只写文字时保留左侧页眉。文字可加粗，图片应直接插入，不要包在链接或加粗标记内。单页可用 `<!-- _header: "" -->` 隐藏整条页眉；`_header` 会覆盖全局内容，若要改标题并保留校徽，请写 `<!-- _header: "实验结果 ![](./themes/assets/xmu_logo_name.svg)" -->`。封面、目录、导航栏保留专用布局。

---

##### <mark>注意</mark>: 主题资源文件路径问题

- 校徽路径现在写在 Markdown 的 `header` 中，相对于源文件解析，不再写入主题 SCSS。
- 仓库根目录的文档使用 `./themes/assets/xmu_logo_name.svg`；`examples/` 或 `workspace/` 下的文档使用 `../themes/assets/xmu_logo_name.svg`。
- CLI 导出 PDF/图片需要 `--allow-local-files`，并通过 `--theme-set themes/am_template.scss themes/am_xmu.scss` 同时加载两个主题。
- 导出 HTML 建议放在 Markdown 同目录；移动或分享 HTML 时仍需携带图片并保持相对路径有效。

以下是旧版在主题中误用相对路径时的报错信息，供排查资源路径参考:

```log
log.ts:460   ERR Webview.loadLocalResource - Error using fileReader. 
    requestUri=file:///Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg, 
    resourceToLoad=file:///Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg 
......
index.html:1  GET https://file+.vscode-resource.vscode-cdn.net/Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg 404 (Not Found)
```

## HTML小技巧

---

### 图片过高的历史示例

<!-- _class: cols-2 -->
在下面的两列布局例子下, 图片过高
如果直接使用`cols-2`类, 让二者对齐, 会要导致图表下移, 显示不全
常规处理应先限制图片高度、减少正文或调整原生布局，参见 [Agent 指南](themes/AGENT_GUIDE.md)。

<div class="ldiv">

- 这是八奈见杏菜
- 她很可爱
- 请喂她零食

</div>

<div class="rimg" style="flex-direction: column; ">

<img src="./Marp主题使用与编辑.assets/YanamiAnna.png" alt="YanamiAnna" height="550" />

</div>

---

### 负 margin 定位：特殊补救手段

<!-- _class: cols-2 -->
在下面的两列布局例子下, 图片过高
如果直接使用`cols-2`类, 让二者对齐, 会要导致图表下移, 显示不全
以下保留历史定位技巧；仅在原生布局与图片尺寸调整仍无法满足需求时使用，必须重新检查遮挡和溢出。

<div class="ldiv">

- 这是八奈见杏菜
- 她很可爱
- 请喂她零食

</div>

<div class="rimg" style="flex-direction: column; margin-top: -10rem;">

<img src="./Marp主题使用与编辑.assets/YanamiAnna.png" alt="YanamiAnna" height="550" />

</div>

---

### 插入图标

因为Marp支持内嵌HTML, 可以使用[fontawesome](https://fontawesome.com/icons)去添加图标, 例如

- <i class="fa-brands fa-fly"></i> 这是一个热气球
- <i class="fa-solid fa-person-running"></i> 这是一个跑步的人
- <i class="fa-brands fa-github"></i> 这是GitHub图标

---

### Mermaid

<div class="mermaid">
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
</div>

<!-- mermaid.js -->
<script src="https://unpkg.com/mermaid@8.1.0/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>

---
<!-- _class: lastpage -->

###### Thank You
