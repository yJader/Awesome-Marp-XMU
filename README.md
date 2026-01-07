> [!IMPORTANT]
> 本项目基于 [Awesome Marp](https://github.com/favourhong/Awesome-Marp) v1.3, 进行了以下修改
>

## template改动

### 修复与增强

1. 参考[PKU主题](https://github.com/goudanZ1/Awesome-Marp), 修改字号为固定px;
2. 修复`bq-xxx`类引用块在使用列表时, 背景色无法正确显示的bug;
3. 增强所有布局类的适配性:
   - **`cols-*` 系列**: 在`.ldiv`和`.rdiv`前后添加内容时, 会自动占据空间, 避免重叠和布局错乱
   - **`rows-2` 和 `pin-3` 布局**: 修复标题被内容覆盖的问题，改为自适应高度的灵活布局
   - **图片容器**: 所有图片容器(`.limg`, `.rimg`, `.timg`, `.bimg`等)内的文本描述会自动换行并居中显示
4. 修复`fixedtitleB`与分栏布局组合使用时的冲突，标题背景宽度改为自适应;

### 新增

1. 在`am_template.scss`中新增变量`--gap-cols`，可统一控制所有分栏布局的间距;
2. 新增`pin-3-inv`类，实现倒置品字型分栏布局:
   - 中间栏在下，两侧栏在上，适合展示顶部对称内容和底部重点内容的场景

### TODO

1. 增加`_class: ignore` 类, 隐藏当前页面, 适用于草稿和备注页面
    - 但是通过css可能无法完全隐藏

## XMU主题开发

添加了一套 [XMU 主题的模版 am_xmu](files/AwesomeMarp_xmu.pdf)

![AwesomeMarp_xmu](./README.assets/AwesomeMarp_xmu.gif)

- 没有安装额外字体, 感觉黑体更严肃一些, 也不错XD
- 调整主题颜色, 添加校徽资源
- 在am_xmu主题中修复了am_template中封面页(cover_c, cover_e)中, 不适配不同大小校徽的bug(暂未在am_template中直接修改)

## 安装与使用

### Marp for VS Code 使用

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
    - 更详细的样式说明 请参考<mark>官方文档[Awesome Marp主题说明](./examples/AwesomeMarp_xmu.md)</mark>

### 常见bug

#### 渲染html

本模板中大量使用了html标签(如`<div>`), 以实现更复杂的布局和样式, 因此需要开启Marp的html渲染功能

因此参考[settings.json](./.vscode/settings.json) 和 [官方README](https://github.com/marp-team/marp-vscode?tab=readme-ov-file#html-elements-in-markdown-%EF%B8%8F) 说明, 需要

- 新版插件(since v2): 在VS Code的设置中开启`markdown.marp.html`选项, 设置为`all`
- 旧版插件: 在VS Code的设置中开启`markdown.marp.enableHtml`选项, 设置为`true`

### 额外说明

我编写了一个 **[说明文档](./Marp主题使用与编辑.md)**, 记录一些更复杂的使用过程和DIY模板经验

此外也可以参考我的博客: [Plain Text is All You Need (for Presentations)](https://yjader.github.io/JinBlog/blog/presentation.html#plain-text-is-all-you-need-for-presentations), 里面有其他使用Marp的演讲经验分享

## 下载方式

为加速下载，同时提供 **GitHub** 与 **Gitee** 两个镜像仓库： [Awesome-Marp-XMU (GitHub)](https://github.com/yJader/Awesome-Marp-XMU)￼ / [Awesome-Marp-XMU (Gitee)￼](https://gitee.com/yJader/Awesome-Marp-XMU)

<mark>在此感谢原作者开源QAQ, 光速完成日常汇报</mark>

---

> **以下是原仓库的 README 文件:**

[✨ README-en](./README-origin-en.md)、[🎉 README-zh](./README-origin.md)
