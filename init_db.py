#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建筑构造数据库初始化
运行: python init_db.py
"""

import os
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / 'construction.db'
SCHEMA   = BASE_DIR / 'init_schema.sql'

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(open(SCHEMA, encoding='utf-8').read())
    conn.commit()
    print(f"表结构创建完成: {DB_PATH}")
    return conn

def seed_categories(conn):
    pass  # 已由 schema 初始化

def seed_methods(conn):
    """种子数据：构造做法"""
    cats = {r['code']: r['id'] for r in conn.execute('SELECT code, id FROM categories').fetchall()}

    methods = [
        # ── 屋面 ──
        {
            'code': 'ROOF_FLAT_TRAFFIC', 'name': '平屋面正置式（上人）',
            'category_id': cats['roof'], 'sub_type': '正置式/上人',
            'short_desc': 'SBS改性沥青两道设防 + XPS保温 + 细石混凝土保护层',
            'applicable': '住宅/办公上人屋面，需考虑后期维护荷载',
            'climate_zone': '严寒/寒冷/夏热冬冷',
            'waterproof_grade': 'I级', 'cost_tier': '中', 'unit_cost': 380,
            'fire_grade': 'A级（保护层）',
            'key_sizes': json.dumps({
                '防水层': '4+3mm SBS两道设防',
                '保温层': 'XPS 80~120mm',
                '找坡': '2%（轻骨料混凝土）',
                '隔汽层': '严寒/寒冷必需',
                '泛水高度': '≥250mm'
            }),
            'source_doc': '构造图集/屋面节点/平屋面-标准做法.md',
            'remark': '主流做法，造价适中，保温材料可选XPS/EPS/岩棉'
        },
        {
            'code': 'ROOF_FLAT_INVERTED', 'name': '平屋面倒置式',
            'category_id': cats['roof'], 'sub_type': '倒置式',
            'short_desc': '防水层在下，XPS保温压载在上，延长防水寿命',
            'applicable': '对防水寿命要求高的项目（地标/品质项目）',
            'climate_zone': '严寒/寒冷/夏热冬冷/夏热冬暖',
            'waterproof_grade': 'I级', 'cost_tier': '中高', 'unit_cost': 480,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '保温层': 'XPS 100~150mm（必须用XPS，EPS不可）',
                '压载层': '卵石或混凝土板 50~80mm',
                '找坡': '2~3%',
                '保温要求': '吸水率≤1%'
            }),
            'source_doc': '构造图集/屋面节点/平屋面-标准做法.md',
            'remark': '防水层被保温层保护，寿命延长；但保温材料受限'
        },
        {
            'code': 'ROOF_FLAT_NON_TRAFFIC', 'name': '平屋面正置式（不上人）',
            'category_id': cats['roof'], 'sub_type': '正置式/不上人',
            'short_desc': 'SBS卷材+保温+找坡，无保护层或仅涂料保护',
            'applicable': '不上人屋面，住宅闷顶/工业辅助屋面',
            'climate_zone': '严寒/寒冷',
            'waterproof_grade': 'II级', 'cost_tier': '低', 'unit_cost': 280,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '保温': 'EPS 60~100mm 或 XPS',
                '找坡': '2~3%',
                '反射层': '反射率≥0.6'
            }),
            'source_doc': '构造图集/屋面节点/平屋面-标准做法.md'
        },
        {
            'code': 'ROOF_SLOPE_METAL', 'name': '坡屋面（金属压型板）',
            'category_id': cats['roof'], 'sub_type': '坡屋面/金属',
            'short_desc': '铝合金/镀锌钢板压型板 + 岩棉保温',
            'applicable': '工业厂房/仓库/低层公建',
            'climate_zone': '通用',
            'waterproof_grade': 'II级', 'cost_tier': '中', 'unit_cost': 350,
            'fire_grade': 'A级（岩棉）',
            'key_sizes': json.dumps({
                '压型板': '0.6~1.2mm',
                '保温': '岩棉/玻璃棉 100~200mm',
                '坡度': '≥10%（约6°）'
            })
        },
        {
            'code': 'ROOF_GREEN', 'name': '绿化屋面（花园式）',
            'category_id': cats['roof'], 'sub_type': '绿化屋面',
            'short_desc': '植被+种植土+排水板+耐根穿刺防水',
            'applicable': '高端住宅/公建屋顶花园',
            'climate_zone': '通用',
            'waterproof_grade': 'I级', 'cost_tier': '高', 'unit_cost': 880,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '种植基质': '300~600mm',
                '排水层': '≥25mm',
                '耐根穿刺层': '必须设置',
                '防水层': '≥2道'
            }),
            'remark': '必须设耐根穿刺层 + 普通防水层（≥2道）'
        },
        {
            'code': 'ROOF_BIPV', 'name': '光伏屋面（BIPV一体化）',
            'category_id': cats['roof'], 'sub_type': '光伏屋面',
            'short_desc': '光伏组件兼做屋面 + TPO防水',
            'applicable': '绿色建筑/双碳项目',
            'climate_zone': '通用',
            'waterproof_grade': 'I级', 'cost_tier': '高', 'unit_cost': 1200,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '光伏组件': '转换效率≥18%',
                '倾角': '15°~35°',
                '防水': 'TPO/PVC热风焊接'
            })
        },
        # ── 墙体 ──
        {
            'code': 'WALL_BRICK_INSULATION', 'name': '烧结多孔砖外墙外保温',
            'category_id': cats['wall'], 'sub_type': '承重墙/外保温',
            'short_desc': '240mm烧结多孔砖 + EPS/岩棉外保温 + 弹性涂料',
            'applicable': '多层住宅主流做法',
            'climate_zone': '严寒/寒冷/夏热冬冷',
            'waterproof_grade': None, 'cost_tier': '中', 'unit_cost': 320,
            'fire_grade': 'A级（岩棉）/B1级（EPS）',
            'key_sizes': json.dumps({
                '砖墙厚度': '240mm',
                '保温': '严寒/寒冷≥80mm，夏热冬冷≥60mm',
                '圈梁': '每层设，高≥120mm',
                '构造柱': '墙端/转角/长>5m'
            }),
            'source_doc': '构造图集/墙体节点/墙体构造-标准做法.md',
            'remark': '高层禁用EPS保温，必须A级岩棉'
        },
        {
            'code': 'WALL_AERATED_INSULATION', 'name': '加气混凝土砌块外墙',
            'category_id': cats['wall'], 'sub_type': '框架填充/外保温',
            'short_desc': '200~300mm加气混凝土砌块 + 外保温',
            'applicable': '框架结构填充墙主流做法',
            'climate_zone': '通用',
            'cost_tier': '中', 'unit_cost': 280,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '砌块强度': 'A3.5/A5.0',
                '灰缝': '≤3mm（专用粘结剂）',
                '拉结筋': '2Φ6@500',
                '构造柱': '墙长>5m设'
            })
        },
        {
            'code': 'WALL_SHEAR_INSULATION', 'name': '钢筋混凝土剪力墙外保温',
            'category_id': cats['wall'], 'sub_type': '剪力墙/外保温',
            'short_desc': 'C30剪力墙 + 岩棉A级保温（高层必A）',
            'applicable': '高层住宅/办公',
            'climate_zone': '严寒/寒冷',
            'cost_tier': '中', 'unit_cost': 360,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '墙厚': '200~250mm（按结构计算）',
                '保温': '严寒≥120mm，寒冷≥100mm',
                '防火隔离带': '每2-3层设300mm高A级'
            })
        },
        {
            'code': 'WALL_EPS_THIN', 'name': 'EPS板薄抹灰外墙外保温',
            'category_id': cats['wall'], 'sub_type': '外保温/薄抹灰',
            'short_desc': 'EPS板+聚合物砂浆+网格布+涂料',
            'applicable': '经济型项目，仅限≤27m建筑',
            'climate_zone': '夏热冬冷/夏热冬暖',
            'cost_tier': '低', 'unit_cost': 180,
            'fire_grade': 'B1级',
            'key_sizes': json.dumps({
                'EPS密度': '≥18kg/m³',
                '板缝': '≤2mm',
                '高层': '禁用'
            })
        },
        {
            'code': 'WALL_ROCKWOOL_THIN', 'name': '岩棉板薄抹灰外墙外保温（主流）',
            'category_id': cats['wall'], 'sub_type': '外保温/薄抹灰/防火型',
            'short_desc': '岩棉板+聚合物砂浆+网格布+弹性涂料',
            'applicable': '高层/超高层首选防火型保温',
            'climate_zone': '严寒/寒冷',
            'cost_tier': '中高', 'unit_cost': 280,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '岩棉密度': '垂直纤维≥140kg/m³',
                '锚栓': '首层≥10个/m²，标准层≥8个/m²',
                '防火隔离带': '每2-3层300mm高A级'
            })
        },
        # ── 楼地面 ──
        {
            'code': 'FLOOR_RESIDENTIAL_WOOD', 'name': '住宅卧室强化木地板',
            'category_id': cats['floor'], 'sub_type': '住宅/木地板',
            'short_desc': '强化木地板+防潮膜+找平层',
            'applicable': '住宅卧室/起居室',
            'cost_tier': '低', 'unit_cost': 180,
            'key_sizes': json.dumps({
                '木地板': '8~12mm',
                '找平层': '30mm',
                '防潮膜': '上翻50mm'
            })
        },
        {
            'code': 'FLOOR_RESIDENTIAL_TILE', 'name': '住宅客厅瓷砖',
            'category_id': cats['floor'], 'sub_type': '住宅/瓷砖',
            'short_desc': '瓷砖+粘结层+找平层',
            'applicable': '住宅客厅/餐厅',
            'cost_tier': '中', 'unit_cost': 220,
            'key_sizes': json.dumps({
                '瓷砖': '8~10mm',
                '粘结层': '10~15mm',
                '找平层': '20~30mm'
            })
        },
        {
            'code': 'FLOOR_BATHROOM', 'name': '住宅卫生间防水楼面',
            'category_id': cats['floor'], 'sub_type': '住宅/防水',
            'short_desc': '防滑瓷砖+JS防水涂料+找坡',
            'applicable': '住宅卫生间',
            'cost_tier': '中', 'unit_cost': 280,
            'waterproof_grade': 'I级',
            'key_sizes': json.dumps({
                '防水': 'JS聚合物水泥1.5mm',
                '上翻高度': '淋浴区1.8m，非淋浴0.3m',
                '找坡': '1~2%坡向地漏',
                '蓄水试验': '24h'
            })
        },
        {
            'code': 'FLOOR_OFFICE_RAISED', 'name': '办公架空地板',
            'category_id': cats['floor'], 'sub_type': '办公/架空',
            'short_desc': '钢质/硫酸钙架空地板+可调支架',
            'applicable': '大型办公/数据中心',
            'cost_tier': '中高', 'unit_cost': 380,
            'key_sizes': json.dumps({
                '地板': '35~40mm',
                '支架高度': '150~300mm（按线槽）'
            })
        },
        {
            'code': 'FLOOR_SOUND_INSULATION', 'name': '住宅分户楼板（隔声强条）',
            'category_id': cats['floor'], 'sub_type': '住宅/隔声',
            'short_desc': '隔声垫+细石混凝土+面层',
            'applicable': '分户楼板（强条要求）',
            'cost_tier': '中高', 'unit_cost': 320,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '板厚': '120mm',
                '隔声垫': '8mm',
                '细石混凝土': '50mm',
                '撞击声压级': '≤75dB（强条）'
            }),
            'remark': 'GB 50118-2010 民用建筑隔声设计规范 强条'
        },
        {
            'code': 'FLOOR_HEATING_WATER', 'name': '水暖地暖楼面',
            'category_id': cats['floor'], 'sub_type': '地暖',
            'short_desc': '地暖管+反射膜+XPS+填充层+面层',
            'applicable': '住宅/精装地暖',
            'cost_tier': '中高', 'unit_cost': 420,
            'key_sizes': json.dumps({
                '盘管间距': '150~200mm',
                '保温': 'XPS 20~30mm',
                '填充层': '30~40mm'
            })
        },
        # ── 基础 ──
        {
            'code': 'FOUNDATION_STRIP', 'name': '条形基础',
            'category_id': cats['foundation'], 'sub_type': '浅基础',
            'short_desc': '砖/混凝土条形基础',
            'applicable': '多层砖混结构',
            'cost_tier': '低', 'unit_cost': 800,
            'key_sizes': json.dumps({
                '埋深': '≥0.5m（冻土线以下）',
                '宽度': '由计算确定',
                '防潮层': '-0.060m'
            })
        },
        {
            'code': 'FOUNDATION_RAFT', 'name': '筏板基础',
            'category_id': cats['foundation'], 'sub_type': '浅基础',
            'short_desc': '整体筏板',
            'applicable': '高层/软土地基',
            'cost_tier': '高', 'unit_cost': 1500
        },
        # ── 变形缝 ──
        {
            'code': 'JOINT_EXPANSION', 'name': '伸缩缝',
            'category_id': cats['joint'], 'sub_type': '温度变形',
            'short_desc': '温度缝，墙体双面+板双面留缝',
            'applicable': '房屋长度>50m时设',
            'cost_tier': '中', 'unit_cost': 200,
            'key_sizes': json.dumps({
                '缝宽': '20~30mm',
                '构造': '弹性盖板+嵌缝胶'
            })
        },
        {
            'code': 'JOINT_SETTLEMENT', 'name': '沉降缝',
            'category_id': cats['joint'], 'sub_type': '不均匀沉降',
            'short_desc': '从基础到屋顶全断',
            'applicable': '地基土质差异大/荷载差异大',
            'cost_tier': '中高', 'unit_cost': 350,
            'key_sizes': json.dumps({
                '缝宽': '30~70mm（多层）/ ≥120mm（高层）',
                '构造': '从基础到屋顶全断'
            })
        },
        {
            'code': 'JOINT_SEISMIC', 'name': '防震缝',
            'category_id': cats['joint'], 'sub_type': '地震设防',
            'short_desc': '按计算设缝，全断+双柱双墙',
            'applicable': '体型复杂/刚度差异大',
            'cost_tier': '中高', 'unit_cost': 380,
            'key_sizes': json.dumps({
                '缝宽': '框架70mm+/框剪100mm+/剪力墙1/120高度',
                '构造': '全断+双柱/双墙'
            })
        },
        # ── 幕墙 ──
        {
            'code': 'CURTAIN_GLASS_EXPOSED', 'name': '玻璃幕墙（明框）',
            'category_id': cats['curtain'], 'sub_type': '玻璃/明框',
            'short_desc': '铝合金型材压板外露50~60mm',
            'applicable': '高层办公/商业幕墙',
            'cost_tier': '中高', 'unit_cost': 1100,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '型材外露': '50~60mm',
                '结构清晰': '是',
                '结构胶寿命': '约25年'
            })
        },
        {
            'code': 'CURTAIN_GLASS_HIDDEN', 'name': '玻璃幕墙（隐框）',
            'category_id': cats['curtain'], 'sub_type': '玻璃/隐框',
            'short_desc': '结构胶粘接，外观无缝',
            'applicable': '高端公建',
            'cost_tier': '高', 'unit_cost': 1300,
            'fire_grade': 'A级',
            'remark': '结构胶需定期检测'
        },
        {
            'code': 'CURTAIN_STONE', 'name': '石材幕墙',
            'category_id': cats['curtain'], 'sub_type': '石材',
            'short_desc': '钢龙骨+铝合金挂件+石材',
            'applicable': '高端商业/酒店',
            'cost_tier': '高', 'unit_cost': 1500,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '缝宽': '6~8mm',
                '单块面积': '≤1.5m²',
                '重量': '≤150kg/块'
            })
        },
        {
            'code': 'CURTAIN_DOUBLE', 'name': '双层幕墙（呼吸式）',
            'category_id': cats['curtain'], 'sub_type': '玻璃/双层',
            'short_desc': '双层幕墙+进/出风格栅',
            'applicable': '超高层地标（上海中心）',
            'cost_tier': '高', 'unit_cost': 2800,
            'fire_grade': 'A级',
            'key_sizes': json.dumps({
                '冬季': '温室效应',
                '夏季': '烟囱效应'
            }),
            'remark': '节能性能极佳，造价高'
        },
        # ── 门窗 ──
        {
            'code': 'WINDOW_AL_BROKEN', 'name': '断桥铝合金窗（主流）',
            'category_id': cats['door_win'], 'sub_type': '铝合金/节能',
            'short_desc': '断桥铝型材+中空玻璃',
            'applicable': '住宅/办公主流',
            'cost_tier': '中', 'unit_cost': 800,
            'key_sizes': json.dumps({
                'K值': '≤2.4 W/(m²·K)',
                '玻璃': '5+12A+5',
                '隔声': '≥30dB'
            })
        },
        {
            'code': 'WINDOW_UPVC', 'name': '塑钢窗',
            'category_id': cats['door_win'], 'sub_type': '塑钢',
            'short_desc': 'PVC型材+中空玻璃',
            'applicable': '经济型住宅',
            'cost_tier': '低', 'unit_cost': 480,
            'fire_grade': 'B2级'
        },
    ]

    for m in methods:
        cols = ', '.join(m.keys())
        ph   = ', '.join(['?'] * len(m))
        conn.execute(f'INSERT OR REPLACE INTO construction_methods ({cols}) VALUES ({ph})',
                      list(m.values()))

    conn.commit()
    print(f"构造做法: {len(methods)} 条")

def seed_layers(conn):
    """层次表数据"""
    # 先清空（防重插）
    conn.execute('DELETE FROM layers')

    method_codes = {}
    for r in conn.execute('SELECT code, id FROM construction_methods').fetchall():
        method_codes[r['code']] = r['id']

    # 平屋面正置式（上人）
    flat_traffic = [
        (1, '面层/保护层',     'C20细石混凝土(配Φ4@200钢丝网)', '40',     '—',                        '分格缝≤6m×6m', 'top_down'),
        (2, '隔离层',          '无纺布或PE膜',                  '—',     '—',                        '—',             'top_down'),
        (3, '防水层',          'SBS改性沥青卷材(II型)',         '4+3',   'I级两道设防',                '或TPO/PVC 1.5×2','top_down'),
        (4, '找平层',          '1:3水泥砂浆',                  '20',     '—',                        '设分格缝',       'top_down'),
        (5, '保温层',          'XPS挤塑板',                    '80~120', 'λ≤0.030 W/(m·K)',         '厚度按热工计算', 'top_down'),
        (6, '找坡层',          '轻骨料混凝土',                  '最薄30', '—',                        '找2%坡',         'top_down'),
        (7, '隔汽层',          'PVC隔汽膜',                    '0.3',    '—',                        '严寒/寒冷必需',  'top_down'),
        (8, '结构层',          '钢筋混凝土屋面板',              '120~150','—',                       '按结构计算',     'top_down'),
    ]

    # 平屋面倒置式
    flat_inv = [
        (1, '保护层/压载层',    '卵石或C20混凝土板',           '50~80',  '—',                        '卵石20~30mm',   'top_down'),
        (2, '过滤层',          '聚酯无纺布',                  '—',     '—',                          '防止细料堵塞',  'top_down'),
        (3, '保温层',          'XPS挤塑板(必须XPS)',          '100~150','λ≤0.030,吸水率≤1%',       'EPS不可',       'top_down'),
        (4, '防水层',          'SBS改性沥青或TPO卷材',        '4+3',   '—',                          '保温层保护防水', 'top_down'),
        (5, '找平层',          '1:3水泥砂浆',                 '20',    '—',                          '—',             'top_down'),
        (6, '找坡层',          '轻骨料混凝土',                 '最薄30','坡度2%~3%',                '—',             'top_down'),
        (7, '结构层',          '钢筋混凝土屋面板',             '120~150','—',                         '按结构计算',    'top_down'),
    ]

    # 绿化屋面
    green = [
        (1, '植被层',          '灌木/草坪/地被',              '200~500','—',                        '按设计',        'top_down'),
        (2, '种植基质',         '轻质种植土',                  '300~600','容重≤1200kg/m³',         '蓄排水兼顾',    'top_down'),
        (3, '过滤层',          '聚酯无纺布',                  '—',     '—',                          '防基质流失',    'top_down'),
        (4, '排水层',          '排水板(凹凸型)',              '≥25',   '排水能力≥2L/s·m²',         '兼蓄水',        'top_down'),
        (5, '耐根穿刺层',      '铜离子复合胎基SBS/TPO/PVC',    '4',     '耐根穿刺',                   '必须设置',      'top_down'),
        (6, '普通防水层',      'SBS/TPO/PVC卷材',             '4+3',   'I级两道设防',               '—',             'top_down'),
        (7, '找平层',          '1:3水泥砂浆',                 '20',    '—',                          '—',             'top_down'),
        (8, '保温层',          'XPS挤塑板',                  '80~120','λ≤0.030',                  '保温兼抗压',    'top_down'),
        (9, '隔汽层',          'PVC隔汽膜',                  '0.3',   '—',                          '—',             'top_down'),
        (10,'结构层',          '钢筋混凝土屋面板',            '≥150',  '—',                         '需加厚',        'top_down'),
    ]

    # 烧结多孔砖外墙
    wall_brick = [
        (1, '饰面层',          '弹性外墙涂料/瓷砖',           '—',     '—',                          '高层瓷砖专项论证','inside_out'),
        (2, '抹面胶浆',         '聚合物胶浆+网格布',           '3~5',   '—',                          '首层加强',      'inside_out'),
        (3, '保温层',          'EPS/岩棉',                  '60~100','按节能计算',                '严寒/寒冷≥80',  'inside_out'),
        (4, '界面剂',          '聚合物界面剂',               '—',     '—',                          '增强粘结',      'inside_out'),
        (5, '墙体',            '烧结多孔砖',                  '240',   '—',                          '错缝砌筑',      'inside_out'),
        (6, '内墙抹灰',         '1:2水泥砂浆',                '20',    '—',                          '—',             'inside_out'),
    ]

    # 卫生间防水楼面
    bathroom = [
        (1, '瓷砖',            '8-10mm防滑瓷砖',             '8~10',  '—',                          '—',             'top_down'),
        (2, '粘结层',          '水泥砂浆/瓷砖胶',             '10~15', '—',                          '—',             'top_down'),
        (3, '保护层',          '1:2.5水泥砂浆',              '15~20', '—',                          '保护防水层',    'top_down'),
        (4, '防水层',          'JS聚合物水泥防水涂料',       '1.5',   '—',                          '淋浴区上翻1.8m','top_down'),
        (5, '找坡层',          '1:3水泥砂浆(1-2%坡)',       '最薄20','—',                          '坡向地漏',      'top_down'),
        (6, '楼板',            '现浇钢筋混凝土',              '100~120','—',                         '—',             'top_down'),
    ]

    # 隔声楼面
    sound = [
        (1, '面层',            '木地板/瓷砖',                 '8~15',  '—',                          '—',             'top_down'),
        (2, '保护层',          '1:2.5细石混凝土',             '35~40', '—',                          '—',             'top_down'),
        (3, '隔声垫',          '玻璃棉/橡胶垫',              '15~20', '—',                          '提升隔声',      'top_down'),
        (4, '楼板',            '现浇钢筋混凝土',              '120~150','—',                         '—',             'top_down'),
    ]

    mapping = {
        'ROOF_FLAT_TRAFFIC': flat_traffic,
        'ROOF_FLAT_INVERTED': flat_inv,
        'ROOF_GREEN': green,
        'WALL_BRICK_INSULATION': wall_brick,
        'FLOOR_BATHROOM': bathroom,
        'FLOOR_SOUND_INSULATION': sound,
    }

    total = 0
    for code, layers in mapping.items():
        if code not in method_codes:
            continue
        mid = method_codes[code]
        for seq, name, mat, thick, perf, remark, direction in layers:
            conn.execute('''
                INSERT INTO layers (method_id, seq, layer_name, material, thickness_mm, performance, remark, direction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [mid, seq, name, mat, thick, perf, remark, direction])
            total += 1

    conn.commit()
    print(f"构造层次: {total} 条")

def seed_regulations(conn):
    """规范依据"""
    regs = [
        {'code': 'GB 50345-2012', 'name': '屋面工程技术规范', 'category': '防水',
         'key_clauses': '第3章 基本规定；第4章 防水工程；第5章 保温工程',
         'issue_year': 2012, 'is_mandatory': 1},
        {'code': 'GB 50176-2016', 'name': '民用建筑热工设计规范', 'category': '保温',
         'key_clauses': '第4章 保温设计；第6章 防潮设计',
         'issue_year': 2016, 'is_mandatory': 1},
        {'code': 'GB 55015-2021', 'name': '建筑节能与可再生能源利用通用规范', 'category': '节能',
         'key_clauses': '第3章 建筑节能；第6章 可再生能源（强条）',
         'issue_year': 2021, 'is_mandatory': 1},
        {'code': 'GB 50016-2014', 'name': '建筑设计防火规范', 'category': '防火',
         'key_clauses': '第5章 民用建筑构造防火；第6章 建筑结构',
         'issue_year': 2014, 'is_mandatory': 1},
        {'code': 'GB 50010-2010', 'name': '混凝土结构设计规范', 'category': '结构',
         'key_clauses': '剪力墙、构造柱、配筋',
         'issue_year': 2010, 'is_mandatory': 1},
        {'code': 'GB 50003-2011', 'name': '砌体结构设计规范', 'category': '结构',
         'key_clauses': '砌体强度、构造柱、圈梁',
         'issue_year': 2011, 'is_mandatory': 1},
        {'code': 'GB 50118-2010', 'name': '民用建筑隔声设计规范', 'category': '隔声',
         'key_clauses': '分户楼板撞击声压级 ≤75dB',
         'issue_year': 2010, 'is_mandatory': 1},
        {'code': 'JGJ 149-2017', 'name': '膨胀聚苯板薄抹灰外墙外保温', 'category': '保温',
         'key_clauses': 'EPS板外保温做法',
         'issue_year': 2017},
        {'code': 'JGJ/T 480-2019', 'name': '岩棉薄抹灰外墙外保温', 'category': '保温',
         'key_clauses': '岩棉板外保温做法',
         'issue_year': 2019},
        {'code': 'JGJ 155-2013', 'name': '种植屋面工程技术规程', 'category': '屋面',
         'key_clauses': '第3章 材料；第5章 构造',
         'issue_year': 2013},
        {'code': 'JGJ 298-2013', 'name': '住宅室内防水工程技术规范', 'category': '防水',
         'key_clauses': '厨卫防水',
         'issue_year': 2013},
        {'code': 'GB 50209-2010', 'name': '建筑地面工程施工质量验收规范', 'category': '楼地面',
         'key_clauses': '楼地面做法',
         'issue_year': 2010},
    ]
    for r in regs:
        conn.execute('''
            INSERT OR REPLACE INTO regulations (code, name, category, key_clauses, issue_year, is_mandatory)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [r['code'], r['name'], r['category'], r['key_clauses'], r['issue_year'], r.get('is_mandatory', 0)])
    conn.commit()
    print(f"规范依据: {len(regs)} 条")

def seed_pitfalls(conn):
    """易错点（高频考点）"""
    conn.execute('DELETE FROM pitfalls')
    cats = {r['code']: r['id'] for r in conn.execute('SELECT code, id FROM categories').fetchall()}
    items = [
        # 屋面
        {'category_id': cats['roof'], 'wrong_statement': '平屋顶不需要找坡',
         'correct': '平屋顶必须找坡，最小坡度2%',
         'importance': '高', 'exam_relevance': 8},
        {'category_id': cats['roof'], 'wrong_statement': '防水层越厚越好',
         'correct': '应按防水等级和材料标准确定，超厚不经济',
         'importance': '中', 'exam_relevance': 6},
        {'category_id': cats['roof'], 'wrong_statement': '绿化屋顶只需要一道防水',
         'correct': '绿化屋顶必须设置耐根穿刺层 + 普通防水层，≥2道',
         'importance': '高', 'exam_relevance': 9},
        {'category_id': cats['roof'], 'wrong_statement': '倒置式保温可以用EPS',
         'correct': '倒置式保温必须用XPS或泡沫玻璃，EPS吸水率高不可用',
         'importance': '高', 'exam_relevance': 8},
        {'category_id': cats['roof'], 'wrong_statement': '保温层可以不做隔汽层',
         'correct': '严寒和寒冷地区必须设置隔汽层',
         'importance': '高', 'exam_relevance': 7},
        {'category_id': cats['roof'], 'wrong_statement': '天沟不需要坡度',
         'correct': '天沟最小坡度1%，坡向雨水口',
         'importance': '中', 'exam_relevance': 6},
        # 墙体
        {'category_id': cats['wall'], 'wrong_statement': '外墙保温越厚越好',
         'correct': '按节能计算确定，过厚反而冷凝风险',
         'importance': '中', 'exam_relevance': 7},
        {'category_id': cats['wall'], 'wrong_statement': '高层也用EPS板保温',
         'correct': '高层禁用EPS，必须A级（岩棉）',
         'importance': '高', 'exam_relevance': 10},
        {'category_id': cats['wall'], 'wrong_statement': '变形缝可只断墙不断板',
         'correct': '温度缝可，沉降/防震缝必须全断',
         'importance': '高', 'exam_relevance': 8},
        {'category_id': cats['wall'], 'wrong_statement': '卫生间防水上翻30cm够了',
         'correct': '淋浴区必须1.8m，非淋浴0.3m',
         'importance': '高', 'exam_relevance': 9},
        {'category_id': cats['wall'], 'wrong_statement': '加气混凝土砌块直接抹灰',
         'correct': '必须先刷界面剂，否则空鼓',
         'importance': '中', 'exam_relevance': 6},
        {'category_id': cats['wall'], 'wrong_statement': '保温层不做防火隔离带',
         'correct': '高层/超高层每2-3层必须设A级隔离带',
         'importance': '高', 'exam_relevance': 8},
        # 楼地面
        {'category_id': cats['floor'], 'wrong_statement': '住宅楼板越厚越好',
         'correct': '按跨度计算，120mm通常够，过厚增加自重',
         'importance': '中', 'exam_relevance': 5},
        {'category_id': cats['floor'], 'wrong_statement': '住宅楼板不用做隔声',
         'correct': '分户楼板必须≤75dB，强条',
         'importance': '高', 'exam_relevance': 9},
        {'category_id': cats['floor'], 'wrong_statement': '木地板直接铺在楼板上',
         'correct': '必须找平+防潮膜，否则起鼓变形',
         'importance': '中', 'exam_relevance': 5},
        {'category_id': cats['floor'], 'wrong_statement': '地暖盘管越密越好',
         'correct': '间距150~200mm，过密阻力大、能耗高',
         'importance': '中', 'exam_relevance': 5},
        {'category_id': cats['floor'], 'wrong_statement': '卫生间地漏可以不找坡',
         'correct': '必须找坡1~2%，排水要求',
         'importance': '高', 'exam_relevance': 8},
    ]
    for i in items:
        conn.execute('''
            INSERT INTO pitfalls (category_id, wrong_statement, correct, importance, exam_relevance)
            VALUES (?, ?, ?, ?, ?)
        ''', [i['category_id'], i['wrong_statement'], i['correct'], i['importance'], i['exam_relevance']])
    conn.commit()
    print(f"易错点: {len(items)} 条")

def seed_exam(conn):
    """考试知识点"""
    items = [
        {'chapter': '4.2', 'section': '4.2.1', 'topic': '屋面防水等级',
         'content': 'I级（重要/高层/大型公共）≥2道；II级（一般）≥1道（GB 50345 第3.0.5条）',
         'difficulty': '易', 'exam_freq': '高',
         'key_point': '记住防水等级与建筑类型的对应'},
        {'chapter': '4.2', 'section': '4.2.2', 'topic': '屋面找坡',
         'content': '平屋面最小坡度2%，结构找坡3~5%；金属板坡屋面≥10%',
         'difficulty': '易', 'exam_freq': '高',
         'key_point': '天沟1%，坡屋面10%'},
        {'chapter': '4.2', 'section': '4.2.3', 'topic': '倒置式屋面保温材料',
         'content': '倒置式保温必须用XPS或泡沫玻璃，EPS不可用（吸水率高）',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '倒置式只能用XPS或泡沫玻璃'},
        {'chapter': '4.2', 'section': '4.2.4', 'topic': '屋面泛水高度',
         'content': '屋面泛水最小高度250mm（GB 50345 第4.11.14条）',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '泛水250mm，女儿墙<800防水收头入墙，≥800需内排水'},
        {'chapter': '4.2', 'section': '4.2.5', 'topic': '外墙保温防火',
         'content': '高层禁用EPS保温，必须A级（岩棉）；每2-3层设300mm高A级防火隔离带',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '高层必A级+防火隔离带'},
        {'chapter': '4.2', 'section': '4.2.6', 'topic': '卫生间防水高度',
         'content': '淋浴区1.8m，非淋浴区0.3m（JGJ 298）',
         'difficulty': '易', 'exam_freq': '高',
         'key_point': '淋浴1.8m，非淋浴0.3m'},
        {'chapter': '4.2', 'section': '4.2.7', 'topic': '变形缝设置',
         'content': '伸缩缝（>50m）、沉降缝（地基差异）、防震缝（体型复杂）',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '温度缝可局部断，沉降/防震缝必须全断'},
        {'chapter': '4.2', 'section': '4.2.8', 'topic': '分户楼板隔声',
         'content': 'GB 50118 强条：分户楼板计权规范化撞击声压级 ≤75dB',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '≤75dB 强条，隔声垫+细石混凝土'},
        {'chapter': '4.2', 'section': '4.2.9', 'topic': '幕墙防火',
         'content': '幕墙与楼板之间必须设防火封堵，防火极限≥1h',
         'difficulty': '中', 'exam_freq': '中',
         'key_point': '防火封堵≥1h，每层设'},
        {'chapter': '4.2', 'section': '4.2.10', 'topic': '门窗K值（传热系数）',
         'content': '居住建筑1~6层≤2.4，7层以上≤2.0 W/(m²·K)',
         'difficulty': '中', 'exam_freq': '中',
         'key_point': '窗墙比与K值要求'},
    ]
    for k in items:
        conn.execute('''
            INSERT OR IGNORE INTO exam_knowledge (chapter, section, topic, content, difficulty, exam_freq, key_point)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [k['chapter'], k['section'], k['topic'], k['content'],
              k['difficulty'], k['exam_freq'], k['key_point']])
    conn.commit()
    print(f"考试知识点: {len(items)} 条")

if __name__ == '__main__':
    print("=" * 50)
    print("建筑构造数据库 TectonicDb - 初始化")
    print("=" * 50)

    conn = init_db()
    seed_methods(conn)
    seed_layers(conn)
    seed_regulations(conn)
    seed_pitfalls(conn)
    seed_exam(conn)

    m = conn.execute('SELECT COUNT(*) FROM construction_methods').fetchone()[0]
    l = conn.execute('SELECT COUNT(*) FROM layers').fetchone()[0]
    r = conn.execute('SELECT COUNT(*) FROM regulations').fetchone()[0]
    p = conn.execute('SELECT COUNT(*) FROM pitfalls').fetchone()[0]
    e = conn.execute('SELECT COUNT(*) FROM exam_knowledge').fetchone()[0]
    c = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]

    print()
    print("数据统计:")
    print(f"  分类: {c}")
    print(f"  构造做法: {m}")
    print(f"  构造层次: {l}")
    print(f"  规范依据: {r}")
    print(f"  易错点: {p}")
    print(f"  考试知识点: {e}")
    print()
    print("数据库初始化完成!")
    print(f"路径: {DB_PATH}")