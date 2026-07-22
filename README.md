# TectonicWeb

建筑构造做法库 · Flask API + SQLite + MCP 调度骨架

## 用途

把 07-Tectonic 目录下的构造做法文件（`.skp` / `.png` / `.pdf` 等）索引进 SQLite，
提供 HTTP API 给前端查询，并预留 MCP 调度接口，让概念图 → AI 识别 → 模型生成
这条链路能跑通。

## 端口

- `5189` — Flask API 直连（`python api_server.py`）
- `8090` — 统一入口（`python start_web.py`），反代 `/api/*` 到 5189，托管静态页面

任一端口都能用，数据来自同一份 `construction.db`。

## 快速跑起来

```bash
pip install -r requirements.txt

# 1. 初始化数据库（首次或重置时）
python init_db.py

# 2. 把 07-Tectonic 下的文件索引进库（--dry-run 先看清单）
python import_07_tectonic.py --dry-run
python import_07_tectonic.py

# 3. 启 API
python api_server.py
# 浏览器开 http://127.0.0.1:5189

# 或启统一入口
python start_web.py
# 浏览器开 http://127.0.0.1:8090
```

## 目录

```
TectonicWeb/
├── api_server.py          # Flask API(5189)
├── start_web.py           # 统一入口(8090)+ 反代
├── mcp_dispatch.py        # MCP 调度骨架(Sketchup/Rhino/Revit)
├── import_07_tectonic.py  # 07-Tectonic 扫描入库
├── init_db.py             # 库结构初始化
├── init_schema.sql        # v1 表结构
├── init_schema_v2.sql     # v2 表结构(三套维度)
├── construction.db        # SQLite 库(进 git,204KB)
├── index.html             # 前端
├── *.py                   # 调试/检查脚本(check_*, test_*, verify_*)
└── media/                 # 缩略图(未启用,目录可空)
```

## 数据库

`construction.db` 走的是 v2 三套维度：

- `dim_part`   — 按建筑部位(Walls/Roof/...)，对应图集册号
- `dim_skill`  — 按工艺技能(防水/保温/...)
- `dim_atlas`  — 按图集编码(D07 / D08 / ...)

同一份文件可命中多个维度，靠 `xref` 表关联。

## MCP 调度骨架

`mcp_dispatch.py` 是占位实现：

- `dispatch(payload)` — 接收前端请求，按 keyword 匹配 `construction_methods.name` + 三维度，返回 top 5 method
- `_call_sketchup_mcp()` / `_call_rhino_mcp()` / `_call_revit_mcp()` — TODO，待三个 MCP 服务实装后接入
- `get_status()` — 看模块当前状态 + TODO 列表

## TODO

- 概念图上传 + vision model 调用
- 三个 MCP 服务（SketchupMcp / RhinoMcp / RevitMcp）实装
- 模型生成进度回调接口
- `media/` 缩略图生成流程（`test_thumb.py` 有原型）
