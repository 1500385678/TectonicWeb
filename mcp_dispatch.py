#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 调度骨架(SketchupMcp / RhinoMcp / RevitMcp)
====================================================

设计目标:
  概念图(渲染图/手绘草图) → AI 识别构造部位 → 在 07-Tectonic 中匹配推荐做法 →
  调用对应 MCP 服务(Sketchup/Rhino/Revit)生成工程模型

当前状态:骨架已搭好,三个 MCP 目录都是空的,需要等"装/写"实际 MCP 服务后再启用真实生成。
本模块提供:
  1. dispatch(payload)         - 主入口,接收前端请求,返回匹配的 method + MCP 调用占位
  2. get_status()              - 模块状态 + TODO 列表
  3. _keyword_match()          - 关键字简单匹配(已可用,做演示)
  4. _call_sketchup_mcp()      - TODO 占位
  5. _call_rhino_mcp()         - TODO 占位
  6. _call_revit_mcp()         - TODO 占位

可立即使用(已实现):
  - 根据输入 keyword 在 construction_methods.name + dim_part.name_zh + dim_atlas.name 中搜索
  - 返回 top 5 匹配 method,带 file_count + atlas_code

待实现(TODO):
  - 概念图上传 + vision model 调用
  - MCP 服务连接(三个目录 _ArchitectLib/{SketchupMcp,RhinoMcp,RevitMcp})
  - 模型生成回调
  - 进度查询接口
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / 'construction.db'


def get_status() -> dict:
    """返回 MCP 模块状态"""
    return {
        'module':     'mcp_dispatch',
        'version':    '0.1.0-skeleton',
        'available':  False,
        'updated':    '2026-07-13',
        'todo': [
            '装/写 SketchupMcp 服务(优先级最高,你有 OrangeSu 插件相关经验)',
            '装/写 RhinoMcp 服务',
            '装/写 RevitMcp 服务',
            '接 vision model 做概念图→部位的 AI 识别',
            '接 MCP 输出→前端展示/下载 SKP',
        ],
        'endpoints': {
            'dispatch':  '/api/mcp/dispatch  POST',
            'status':    '/api/mcp/status    GET',
        },
        'mcp_dirs': {
            'sketchup': 'D:/Mac/Mac/workteam/05_space/03_architect/_ArchitectLib/SketchupMcp/  (空)',
            'rhino':    'D:/Mac/Mac/workteam/05_space/03_architect/_ArchitectLib/RhinoMcp/  (空)',
            'revit':    'D:/Mac/Mac/workteam/05_space/03_architect/_ArchitectLib/RevitMcp/  (空)',
        }
    }


def dispatch(payload: dict) -> dict:
    """
    主入口
    payload = {
        image_url?:   str,   # 概念图(本期未实现,留口)
        keyword?:     str,   # 文本关键字(本期已可用)
        target_model: 'sketchup' | 'rhino' | 'revit' | 'auto',
    }
    """
    keyword      = (payload.get('keyword') or '').strip()
    target_model = payload.get('target_model', 'auto')
    image_url    = payload.get('image_url', '')

    # 1. 调用 AI 识别(占位:目前仅用 keyword 简单搜索)
    if image_url and not keyword:
        keyword = _vision_fallback(image_url)

    # 2. 在数据库匹配 method
    matched = _keyword_match(keyword) if keyword else []

    # 3. 准备 MCP 调用(目前仅返回 TODO)
    mcp_call = _prepare_mcp_call(target_model, matched, keyword)

    return {
        'status':           'matched' if matched else 'no_match',
        'input':            payload,
        'detected_keyword': keyword,
        'matched_methods':  matched,
        'mcp_call':         mcp_call,
        'note':             '本期仅做关键字匹配 + MCP 接口预留,概念图识别 + 真实模型生成待 MCP 服务就位后启用',
        'ts':               datetime.now().isoformat(timespec='seconds'),
    }


def _vision_fallback(image_url: str) -> str:
    """
    概念图 → 关键字(占位)
    TODO: 接入 vision model(如 GPT-4V / Claude 3.5 Sonnet / 通义千问 VL)
    """
    return f'concept-image:{Path(image_url).name if image_url else "?"}'


def _keyword_match(keyword: str, limit: int = 5) -> list[dict]:
    """
    在 construction_methods.name + dim_part.name_zh + dim_atlas.name 中搜索
    """
    if not keyword or not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    kw = f'%{keyword}%'
    rows = conn.execute('''
        SELECT m.id, m.name, m.atlas_code, m.file_count,
               p.name_zh AS part, a.name AS atlas, s.name AS skill
        FROM construction_methods m
        LEFT JOIN dim_part  p ON m.dim_part_id  = p.id
        LEFT JOIN dim_atlas a ON m.dim_atlas_id = a.id
        LEFT JOIN dim_skill s ON m.dim_skill_id = s.id
        WHERE m.file_count > 0 AND (
            m.name LIKE ? OR p.name_zh LIKE ? OR a.name LIKE ? OR s.name LIKE ?
        )
        ORDER BY m.file_count DESC, m.id
        LIMIT ?
    ''', [kw, kw, kw, kw, limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _prepare_mcp_call(target_model: str, matched: list, keyword: str) -> dict:
    """
    准备 MCP 调用(目前是占位)
    TODO: 真实调用时,根据 target_model 路由到:
      - _call_sketchup_mcp(method, params)
      - _call_rhino_mcp(method, params)
      - _call_revit_mcp(method, params)
    """
    router = {
        'sketchup': _call_sketchup_mcp,
        'rhino':    _call_rhino_mcp,
        'revit':    _call_revit_mcp,
    }
    if target_model == 'auto':
        target_model = 'sketchup'  # 默认优先级

    fn = router.get(target_model, _call_sketchup_mcp)

    return {
        'target_model': target_model,
        'callable':     False,  # 真实接通后改 True
        'method_call':  fn.__name__,
        'todo':         f'在 _ArchitectLib/{target_model.title()}Mcp/ 里实现 {fn.__name__}',
        'placeholder_result': {
            'mcp_call_id': None,
            'output_path': None,
            'status':      'pending_implementation',
        }
    }


# ────────────────────────────────────────────────────────────
# MCP 调用占位 - 三个空目录的接入点
# ────────────────────────────────────────────────────────────

def _call_sketchup_mcp(method: dict, params: dict) -> dict:
    """
    TODO: 调用 SketchUp MCP 服务
    计划方案:
      - 在 _ArchitectLib/SketchupMcp/ 写一个 stdio MCP Server(Python)
      - 暴露 tools: insert_component / set_material / create_layer / export_section
      - 通过 Ruby API(已有 OrangeSu 经验)操作 SKP 文件
    """
    return {
        'status':      'not_implemented',
        'message':     'SketchupMcp 服务尚未实现,先在 _ArchitectLib/SketchupMcp/ 写 mcp_server.py',
        'method_id':   method.get('id'),
        'method_name': method.get('name'),
    }


def _call_rhino_mcp(method: dict, params: dict) -> dict:
    """
    TODO: 调用 Rhino MCP 服务
    计划方案: Rhino.Compute(远程调用,需部署) 或 Rhino.Inside + Python 进程内嵌
    """
    return {
        'status':      'not_implemented',
        'message':     'RhinoMcp 服务尚未实现,需要 Rhino.Compute 或 Rhino.Inside',
        'method_id':   method.get('id'),
        'method_name': method.get('name'),
    }


def _call_revit_mcp(method: dict, params: dict) -> dict:
    """
    TODO: 调用 Revit MCP 服务
    计划方案: .NET 8 + ModelContextProtocol.AspNetCore + Revit API(需 Revit 在跑)
    """
    return {
        'status':      'not_implemented',
        'message':     'RevitMcp 服务尚未实现,需要 .NET + Revit API',
        'method_id':   method.get('id'),
        'method_name': method.get('name'),
    }


# ────────────────────────────────────────────────────────────
# CLI 测试
# ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import json
    print('=== MCP 模块状态 ===')
    print(json.dumps(get_status(), ensure_ascii=False, indent=2))
    print()
    print('=== 测试 dispatch(keyword="墙体") ===')
    print(json.dumps(dispatch({'keyword': '墙体', 'target_model': 'sketchup'}), ensure_ascii=False, indent=2))
