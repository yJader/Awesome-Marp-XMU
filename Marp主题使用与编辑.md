---
marp: true
theme: am_xmu
size: 16:9
header: "Marp 主题使用"
# title: "Marp 主题使用"
footer: "\ *亦瑾* &nbsp; *2025年09月30日*"
headingDivider: [2] # 自动根据标题级别添加分割线
---

<!-- markdownlint-disable MD029 MD001 MD033 -->
<!-- _class: cover_e -->
<!-- _header: "![](./themes/assets/xmu_logo.svg)" -->
<!-- _footer: "![](./themes/assets/xmu_slogan.svg)" -->

# Marp主题使用

###### “用法简单、功能全面的个性化 PPT 模板”

在配置和修改Awesome Marp主题时, 碰到了一些坑点, 记录一下
其实这个markdown也是用Marp写的, 可以预览试试XD

## Marp for VS Code 使用

1. 安装`Marp for VS Code`插件
2. 配置`.vscode/settings.json`文件, 指定主题文件路径(可以参考该仓库下的[setting.json](./.vscode/settings.json))
3. 在Markdown文件的YAML头部指定主题, 例如

    ```markdown
    ---
    marp: true
    # 选择am_xmu主题
    theme: am_xmu
    ---
    ```

4. 开始编写(可以提示AI使用Marp语法编写PPT, 高效快速)
    - 更详细的样式说明 请参考<mark>官方文档[Awesome Marp主题说明](./files/AwesomeMarp_xmu.md)</mark>

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
<!-- _footer: "![](./themes/assets/xmu_slogan.svg)" -->
```

2. 模板文件[am_xmu.scss](./themes/am_xmu.scss)的`section::before{background-image: url("themes/assets/xmu_logo_name.svg");}`
   - 如果你觉得在每张图片右上角都加上logo不好看, 可以注释掉XD

---

##### <mark>注意</mark>: 主题资源文件路径问题

- 对于主题需要用到的资源文件(如学校logo图片), 需要使用相对于工作区目录的路径or网络图片路径(如你的oss地址), 不能使用`./`相对于scss文件的路径
- 例如, 在`themes/am_xmu.scss`中
  - 需要使用`background-image: url("themes/assets/xmu_logo.svg");`,
  而不是`background-image: url("./themes/am_xmu.scss");`
  - 这样会被解析为`.../Awesome-Marp-XMU/assets/xmu_logo.svg`,
  而非我们希望的`.../Awesome-Marp-XMU/themes/assets/xmu_logo.svg`

以下是检查vscode控制台的报错信息:

```log
log.ts:460   ERR Webview.loadLocalResource - Error using fileReader. 
    requestUri=file:///Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg, 
    resourceToLoad=file:///Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg 
......
index.html:1  GET https://file+.vscode-resource.vscode-cdn.net/Users/jader/Work/workspace/vscode/Awesome-Marp-XMU/assets/xmu_logo.svg 404 (Not Found)
```

---
<!-- _class: lastpage -->

###### Thank You
