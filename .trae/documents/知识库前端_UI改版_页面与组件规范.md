# 知识库前端 UI 改版：页面布局与组件规范（桌面优先）

## 0. 全局设计目标
- 保持路由与功能不变，仅提升：一致性（组件/间距/反馈）、可读性（层级/对比）、完成度（状态/空态）。

## 1. Global Styles（设计Token建议）
> 可继续沿用现有暗色基调与 CSS 变量命名，但统一“层级/对比/间距”。
- 颜色
  - 背景：bg / panel / panel-2（3层即可，避免过多近似色）
  - 边框：border（统一透明度规则：默认 8%，hover 12%，active 20%）
  - 文本：text / muted（muted 用于说明/次信息/表头）
  - 品牌色：primary（用于主按钮/高亮/焦点环）
  - 状态色：success / warning / danger（用于徽标、提示条）
- 圆角：12（输入/按钮）、16（卡片）、999（pill/badge）
- 阴影：仅卡片/浮层使用一档阴影，避免“处处发光”
- 字体层级
  - PageTitle 18/700；SectionTitle 14/700；Body 14/400；Meta 12/400
- 交互状态
  - Focus：统一 3px 焦点环（primary 10% 透明度）
  - Disabled：统一 55% 不透明 + not-allowed
  - Loading：按钮文案变化 + 不改变布局宽度（避免抖动）

## 2. 布局规范（App Shell）
- 布局方式：Sidebar（固定宽 260px）+ Main（自适应）使用 Flex。
- Main 容器：默认 padding 24；卡片与区域间距 14~18。
- Topbar：左侧“标题+描述”，右侧“主操作/返回/刷新”等；各页面统一 Topbar 结构。
- 响应式：保持现有 <920px 隐藏 Sidebar；Main padding 18；两列 grid2 自动变单列。

## 3. 组件规范（复用类名/视觉行为）
- Card（.card + .cardBody）：作为页面主要承载容器；标题/列表/表单均放入 card。
- Button（.btn）
  - Primary：唯一强调色（提交/发送/前往主流程）
  - Default：次操作（返回/刷新/查看文档）
  - Danger：破坏性操作（删除）
  - Ghost：图标/弱操作（会话删除“×”、侧边栏轻按钮）
- Input（.input）：文本/密码/邮箱统一；file input 建议外包一层说明文本与对齐规则（不强行自定义浏览器按钮）。
- Badge（.badge）：仅用于状态（PROCESSING/COMPLETED/FAILED），颜色与边框规则一致。
- Note/Alert（.note + success/error）：用于成功/错误/提示；建议统一为“信息条”样式：左侧色条+文案（不改变现有文案与逻辑）。
- Table（.table）：表头 muted、小字；行高一致；空状态占一整行。
- Chat
  - bubble：统一最大宽 78%，用户/AI 两种底色；Markdown 内容使用 .md 统一排版。

## 4. Page Specs

### 4.1 /home 主页
- Meta：Title=“主页｜智能知识库”，Description=“上传文档、管理文档、智能问答入口”。
- 结构：Topbar（标题+描述）→ grid2 两张入口卡。
- 入口卡：
  - 标题（SectionTitle）+ 说明（note）+ 操作区（主按钮+次按钮/pill）。
  - 两卡保持同高度，按钮基线对齐。

### 4.2 /upload 上传文档
- Meta：Title=“上传文档｜智能知识库”。
- 结构：Topbar（返回）→ Card → grid2（左：上传表单；右：流程说明）。
- 左侧：file input + 主按钮（上传）+ 状态反馈（error/success）+ 成功后的下一步按钮组。
- 结果回显：JSON 区域使用“代码面板”样式（等宽字体、可滚动、边框清晰）。

### 4.3 /docs 文档管理
- Meta：Title=“文档管理｜智能知识库”。
- 结构：Topbar（返回/刷新）→ Card → Table。
- 表格列：文档名 / 状态徽标 / 失败原因（muted）/ 操作区（删除、file input、重传）。
- 操作区：控件统一高度与间距；busyId 时仅禁用当前行按钮，避免全表不可用。

### 4.4 /chat 智能问答
- Meta：Title=“智能问答｜智能知识库”。
- 结构：左右双卡：左会话列表（固定宽 260）+ 右聊天区（自适应）。
- 左侧会话项：沿用 navItem 样式；选中态与侧边栏一致；“×”按钮使用 ghost，hover 才显著。
- 右侧聊天区：Topbar（标题+描述）→ chatBox（消息流）→ 来源/错误提示 → 输入行（input + 发送）。
- 消息流：
  - 空态文案居中；新消息滚动到底部；Markdown 样式与链接/代码块清晰可辨。

### 4.5 /login 登录
- Meta：Title=“登录｜智能知识库”。
- 结构：Topbar（返回）→ Card → grid2（左表单/右提示）。
- 表单：邮箱、密码、按钮组（登录 primary、去注册 default）；反馈提示使用统一信息条。

### 4.6 /register 注册
- Meta：Title=“注册｜智能知识库”。
- 结构：Topbar（返回/去登录）→ Card → grid2（左表单/右提示）。
- 表单：邮箱、验证码（输入+获取按钮，倒计时状态一致）、密码、注册 primary；反馈提示同登录。
