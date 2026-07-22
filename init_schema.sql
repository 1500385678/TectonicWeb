-- ============================================================
-- 建筑构造数据库 Schema
-- TectonicDb/construction.db
-- 章节 4.2 建筑构造
-- ============================================================

-- ----------------------------------------------------------
-- 1. 部位分类（屋面/墙体/楼地面/基础/变形缝/幕墙/门窗）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    description     TEXT    DEFAULT NULL,
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 2. 构造做法主表（每种做法一张卡）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS construction_methods (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,         -- 'ROOF_FLAT_INVERTED'
    name            TEXT    NOT NULL,                  -- '平屋面倒置式'
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    sub_type        TEXT    DEFAULT NULL,             -- 子类: '正置式/倒置式/上人/不上人'
    short_desc      TEXT    DEFAULT NULL,             -- 一句话描述
    applicable      TEXT    DEFAULT NULL,             -- 适用场景
    climate_zone    TEXT    DEFAULT NULL,             -- '严寒A区/寒冷/夏热冬冷/...'
    waterproof_grade TEXT   DEFAULT NULL,             -- 防水等级 'I/II'
    cost_tier       TEXT    DEFAULT '中',             -- 造价档位
    unit_cost       REAL    DEFAULT 0,                -- 综合造价 元/m²
    fire_grade      TEXT    DEFAULT 'A级',            -- 主要层防火
    key_sizes       TEXT    DEFAULT NULL,             -- 关键尺寸 JSON
    source_doc      TEXT    DEFAULT NULL,             -- 来源文件
    svg_path        TEXT    DEFAULT NULL,             -- SVG 剖面图
    remark          TEXT    DEFAULT NULL,
    status          TEXT    DEFAULT 'active',
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 3. 构造层次表（核心数据，每层一行）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS layers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    method_id       INTEGER NOT NULL REFERENCES construction_methods(id),
    seq             INTEGER NOT NULL,                -- 序号（从上到下 或 从内到外）
    layer_name      TEXT    NOT NULL,                 -- 层名 '保护层'/'保温层'
    material        TEXT    NOT NULL,                 -- 材料/做法
    thickness_mm    TEXT    DEFAULT NULL,             -- 厚度 '40' / '60~100'
    performance     TEXT    DEFAULT NULL,             -- 性能要求
    remark          TEXT    DEFAULT NULL,             -- 备注
    direction       TEXT    DEFAULT 'top_down',        -- 'top_down'(屋面/楼地面) / 'inside_out'(墙体)
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 4. 规范依据表（每条做法可关联多条规范）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS regulations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,           -- 'GB 50345-2012'
    name            TEXT    NOT NULL,
    category        TEXT    DEFAULT NULL,              -- '防水/保温/防火/节能/隔声'
    key_clauses     TEXT    DEFAULT NULL,              -- 关键条文摘要
    full_text       TEXT    DEFAULT NULL,              -- 完整条款（可空）
    issue_year      INTEGER DEFAULT NULL,
    is_mandatory    INTEGER DEFAULT 0,                 -- 是否强条 1/0
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 5. 做法-规范关联表（多对多）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS method_regulations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    method_id       INTEGER NOT NULL REFERENCES construction_methods(id),
    regulation_id   INTEGER NOT NULL REFERENCES regulations(id),
    clause_ref      TEXT    DEFAULT NULL,             -- 具体条款 '第4.11.14条'
    clause_summary  TEXT    DEFAULT NULL              -- 该做法对应的条文摘要
);

-- ----------------------------------------------------------
-- 6. 易错点表（高频考点/常见错误）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS pitfalls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER DEFAULT NULL REFERENCES categories(id),
    wrong_statement TEXT    NOT NULL,                  -- 错误说法
    correct         TEXT    NOT NULL,                  -- 正确做法
    importance      TEXT    DEFAULT '中',              -- 高/中/低
    exam_relevance  INTEGER DEFAULT 0,                 -- 考试相关性 0-10
    source          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 7. 决策规则表（场景→推荐做法）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS decision_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    building_type   TEXT    NOT NULL,                  -- '住宅' / '办公' / '公建' / '工业'
    climate_zone    TEXT    DEFAULT NULL,              -- 气候区
    is_trafficable  TEXT    DEFAULT NULL,              -- '上人' / '不上人' / '绿化'
    special_req     TEXT    DEFAULT NULL,              -- 特殊要求
    recommended_method_id INTEGER NOT NULL REFERENCES construction_methods(id),
    backup_method_id INTEGER DEFAULT NULL REFERENCES construction_methods(id),
    reason          TEXT    DEFAULT NULL,
    priority        INTEGER DEFAULT 5
);

-- ----------------------------------------------------------
-- 8. 考试知识点表（章节4.2）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_knowledge (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter         TEXT    NOT NULL,                  -- '4.2'
    section         TEXT    DEFAULT NULL,              -- '4.2.1'
    topic           TEXT    NOT NULL,
    content         TEXT    NOT NULL,
    difficulty      TEXT    DEFAULT '中',
    exam_freq       TEXT    DEFAULT '中',
    key_point       TEXT    DEFAULT NULL,
    case_example    TEXT    DEFAULT NULL,
    related_method_id INTEGER DEFAULT NULL REFERENCES construction_methods(id)
);

-- ----------------------------------------------------------
-- 9. 节点详图表（标准做法索引）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS detail_drawings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,                  -- '女儿墙泛水节点'
    method_id       INTEGER DEFAULT NULL REFERENCES construction_methods(id),
    category_id     INTEGER DEFAULT NULL REFERENCES categories(id),
    description     TEXT    DEFAULT NULL,
    drawing_path    TEXT    DEFAULT NULL,              -- SVG/PNG 路径
    source_doc      TEXT    DEFAULT NULL,
    status          TEXT    DEFAULT 'pending'          -- 'pending' / 'drawn'
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_methods_category   ON construction_methods(category_id);
CREATE INDEX IF NOT EXISTS idx_methods_code       ON construction_methods(code);
CREATE INDEX IF NOT EXISTS idx_layers_method      ON layers(method_id);
CREATE INDEX IF NOT EXISTS idx_mr_method          ON method_regulations(method_id);
CREATE INDEX IF NOT EXISTS idx_dr_category        ON decision_rules(category_id);
CREATE INDEX IF NOT EXISTS idx_layers_seq         ON layers(method_id, seq);

-- ============================================================
-- 初始数据：分类
-- ============================================================
INSERT OR IGNORE INTO categories (code, name, description, sort_order) VALUES
    ('roof',     '屋面',     '平屋面/坡屋面/绿化屋面/光伏屋面', 1),
    ('wall',     '墙体',     '外墙承重/外保温/防潮层/变形缝', 2),
    ('floor',    '楼地面',   '楼板结构/楼面做法/隔声楼面/地暖', 3),
    ('foundation','基础',    '基础埋深/防潮/散水', 4),
    ('joint',    '变形缝',   '伸缩缝/沉降缝/防震缝/盖缝构造', 5),
    ('curtain',  '幕墙',     '玻璃/石材/金属板/陶板幕墙', 6),
    ('door_win', '门窗',     '铝合金/断桥铝/塑钢/木/钢', 7);