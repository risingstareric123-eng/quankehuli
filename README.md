# Journal Editor Autopilot（期刊编辑自动化程序）

离线运行的医学护理稿件技术编辑/文字编辑工具。输入 `.docx` 稿件，输出：

- `edited.docx`（编辑后文稿）
- `report.json`（结构化校对报告）
- `report.md`（可读报告）
- `changes.md`（逐条修改对照）
- `diff.html`（段落级差异）

## 环境

- Python 3.11

## 安装

```bash
pip install -r requirements.txt
```

## CLI

```bash
python cli.py --input manuscript.docx --outdir output/ --style nursing_cn --track-changes false
```

可选参数：

- `--aggressive`：更积极润色（默认保守）
- `--config`：指定规则配置文件
- `--citation-style`：`bracket|paren|superscript`

## 功能覆盖

### 1) 语言润色（安全最小改写）

- 句内标点规范化（中英文标点统一）
- 重复标点、空格、数字与单位间隔规范
- 缩写规范（如 BMI、SBP）
- 保守模式下不改动数字、单位、药名、统计量、结论方向

### 2) 一致性检查

- 摘要与正文：样本量 `n=`、目的/方法/结果/结论关键词映射
- 术语/单位一致性（同一变量多单位告警）
- 图表与正文引用一致性
- 参考文献引用序号与文末条目数一致性

### 3) 编号/结构/格式检查

- 标题编号连续性（如 1,2,3）
- 结构完整性（题名/摘要/关键词/引言/方法/结果/讨论/结论/参考文献/伦理声明等）
- 表内百分比合计误差检查（配置容差）

## 自动修复 vs 只提示

**自动修复（当前实现）**
- 轻量语言与标点规范化
- 数字与单位间空格
- 缩写大小写统一（规则内）

**只提示（当前实现）**
- 摘要-正文关键数据不一致
- 引用跳号/重复/总数不匹配
- 同指标多单位冲突
- 表格百分比合计异常
- 图表未被正文引用
- 结构缺项

## 扩展规则

编辑 `rules/sample_config.json`（运行默认）或参考 `rules/sample_config.yaml`（示例模板） ：

- `required_sections`：增减结构必检项
- `unit_whitelist`：单位白名单
- `percent_tolerance`：百分比合计允许误差
- `citation_style`：引用风格目标（后续可扩展到自动格式化）

## 测试

```bash
pytest -q
```

测试覆盖：

- 编号连续性检测
- 单位冲突检测
- 摘要一致性检测
