---
marp: true
theme: am_xmu
size: 16:9
header: "Marp 主题使用"
# title: "Marp 主题使用"
footer: "亦瑾"
headingDivider: [2] # 自动根据标题级别添加分割线
---

<!-- markdownlint-disable MD029 -->

# Marp主题使用

> 在配置和修改Awesome Marp主题时, 碰到了一些坑点, 记录一下
>
> 其实这个markdown也是用Marp写的, 可以预览试试XD

## Marp for VS Code 使用

1. 安装`Marp for VS Code`插件
2. 配置`.vscode/settings.json`文件, 指定主题文件路径(可以参考该仓库下的[setting.json](./.vscode/settings.json))

---

3. 在Markdown文件的YAML头部指定主题, 例如

    ```markdown
    ---

    marp: true
    # 选择am_xmu主题
    theme: am_xmu
    size: 16:9
    header: "这是页眉, 我一般放PPT标题"
    title: "这是标题, 效果等于`# xxx`"
    footer: "这是页脚, 我一般放作者名" 
    headingDivider: [2] # 自动根据标题级别添加分割线

    ---
    ```

4. 开始编写(可以提示AI使用Marp语法编写PPT, 高效快速)

## 主题编辑

### 主题资源文件路径问题

- 对于主题需要用到的资源文件(如学校logo图片), 需要使用相对于工作区目录的路径or网络图片路径(如你的oss地址), 不能使用`./`相对于scss文件的路径
- 例如, 在`themes/am_xmu.scss`中
  - 需要使用`background-image: url("themes/assets/xmu_logo.svg");`,
  而不是`background-image: url("./themes/am_xmu.scss");`
  - 这样会被解析为`.../Awesome-Marp-XMU/assets/xmu_logo.svg`,
  而非我们希望的`.../Awesome-Marp-XMU/themes/assets/xmu_logo.svg`

---
以下是检查vscode控制台的报错信息:

```log
log.ts:460   ERR Webview.loadLocalResource - Error using fileReader. requestUri=file:///Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg, resourceToLoad=file:///Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg 
error @ log.ts:460
error @ log.ts:565
error @ logService.ts:51
nbn @ resourceLoading.ts:82
await in nbn
yb @ webviewElement.ts:762
(anonymous) @ webviewElement.ts:282
(anonymous) @ webviewElement.ts:518
H.onmessage @ webviewElement.ts:518
index.html:1  GET https://file+.vscode-resource.vscode-cdn.net/Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg 404 (Not Found)
```
