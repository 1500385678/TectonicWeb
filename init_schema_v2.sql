-- ============================================================
-- 建筑构造数据库 Schema v2 增量
-- TectonicDb/construction.db
-- 用于: 07-Tectonic 三套分类口径 + 原始文件登记
-- 兼容性: 在 v1 基础上 ALTER,不破坏现有数据
-- ============================================================

-- ----------------------------------------------------------
-- 10. 维度表1: 10 大部件(原 07-Tectonic/001_Walls 之类)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_part (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,        -- '001_Walls'
    name_zh         TEXT    NOT NULL,                -- '墙体'
    name_en         TEXT    DEFAULT NULL,            -- 'Walls'
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 11. 维度表2: 技能库(原 07-Tectonic/archi-*)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_skill (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,        -- 'archi-tectonic'
    name            TEXT    NOT NULL,                -- '构造做法'
    description     TEXT    DEFAULT NULL,
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 12. 维度表3: 构造图集(原 07-Tectonic/构造图集/*)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_atlas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,        -- '墙体节点'
    name            TEXT    NOT NULL,                -- '墙体节点'
    parent          TEXT    DEFAULT NULL,            -- 父级(预留)
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 13. 构造做法主表扩展(加 dim 字段,允许为空)
-- ----------------------------------------------------------
-- 注意: 不重建 construction_methods,只在 v1 上加列
-- category_id 允许为 NULL(07-Tectonic 文件不一定能映射到 7 个标准 category)
ALTER TABLE construction_methods ADD COLUMN dim_part_id  INTEGER DEFAULT NULL REFERENCES dim_part(id);
ALTER TABLE construction_methods ADD COLUMN dim_skill_id INTEGER DEFAULT NULL REFERENCES dim_skill(id);
ALTER TABLE construction_methods ADD COLUMN dim_atlas_id INTEGER DEFAULT NULL REFERENCES dim_atlas(id);
ALTER TABLE construction_methods ADD COLUMN atlas_code   TEXT    DEFAULT NULL;  -- 原文件里的编号前缀,如 'D07'
ALTER TABLE construction_methods ADD COLUMN file_count   INTEGER DEFAULT 0;    -- 关联文件数(冗余,提速)

-- ----------------------------------------------------------
-- 14. 原始文件登记表
--     每个 PDF/PNG/SKP/RVT/DWG 实体一条
--     不动源文件,只登记路径与元数据
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS tectonic_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    method_id       INTEGER DEFAULT NULL REFERENCES construction_methods(id),
    filename        TEXT    NOT NULL,                -- 'D07+Interseccion+con+angulo+igual+a+90.skp'
    rel_path        TEXT    NOT NULL,                -- 相对 defense/07-Tectonic/ 的路径
    abs_path        TEXT    NOT NULL,                -- 绝对路径
    ext             TEXT    NOT NULL,                -- 'skp' | 'dwg' | 'rvt' | 'pdf' | 'png' | 'svg' | 'md'
    size_kb         INTEGER DEFAULT 0,
    mtime           TEXT    DEFAULT NULL,
    source_type     TEXT    DEFAULT NULL,            -- 'dwg' | 'skp' | 'rvt' | 'pdf' | 'png' | 'svg' | 'md' (同 ext,冗余以便查询)
    role            TEXT    DEFAULT 'other',         -- '节点详图' | '示意图' | '三维模型' | '案例' | '规范' | '说明文档' | 'other'
    group_key       TEXT    DEFAULT NULL,            -- 同一节点的不同格式归为一组: 'D07+Interseccion+...'
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_files_method  ON tectonic_files(method_id);
CREATE INDEX IF NOT EXISTS idx_files_group   ON tectonic_files(group_key);
CREATE INDEX IF NOT EXISTS idx_files_ext     ON tectonic_files(ext);

-- ----------------------------------------------------------
-- 15. 构造做法-维度多对多关联(预留,目前每条记录单维度)
--     留作未来扩展(同一做法可同时归 2~3 个维度)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS method_dim_xref (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    method_id       INTEGER NOT NULL REFERENCES construction_methods(id),
    dim_type        TEXT    NOT NULL,                -- 'part' | 'skill' | 'atlas'
    dim_id          INTEGER NOT NULL,
    UNIQUE(method_id, dim_type, dim_id)
);

-- ----------------------------------------------------------
-- 索引补强
-- ----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_methods_dim_part  ON construction_methods(dim_part_id);
CREATE INDEX IF NOT EXISTS idx_methods_dim_skill ON construction_methods(dim_skill_id);
CREATE INDEX IF NOT EXISTS idx_methods_dim_atlas ON construction_methods(dim_atlas_id);
CREATE INDEX IF NOT EXISTS idx_methods_atlas_code ON construction_methods(atlas_code);

-- ============================================================
-- 种子数据:三套维度初始值
-- 与 07-Tectonic 实际目录一一对应
-- ============================================================

-- 维度1: 10 大部件
INSERT OR IGNORE INTO dim_part (code, name_zh, name_en, sort_order) VALUES
    ('001_Walls',   '墙体',     'Walls',     1),
    ('101_Door',    '门',       'Doors',     2),
    ('201_Windows', '窗',       'Windows',   3),
    ('301_Columns', '柱',       'Columns',   4),
    ('401_Roofs',   '屋面',     'Roofs',     5),
    ('501_Ceiling', '吊顶',     'Ceiling',   6),
    ('601_Floors',  '楼地面',   'Floors',    7),
    ('701_Curtain', '幕墙',     'Curtain Wall', 8),
    ('801_Railing', '栏杆',     'Railing',   9),
    ('901_Stairs',  '楼梯',     'Stairs',    10);

-- 维度2: 技能库
INSERT OR IGNORE INTO dim_skill (code, name, description, sort_order) VALUES
    ('archi-tectonic',     '构造总论',     '构造做法总体框架与决策规则', 1),
    ('archi-door-window',  '门窗专项',     '门/窗设计、性能、供应商', 2),
    ('archi-roof',         '屋面专项',     '屋面构造、防水、节点',     3);

-- 维度3: 构造图集(7 个节点类型)
INSERT OR IGNORE INTO dim_atlas (code, name, parent, sort_order) VALUES
    ('变形缝节点', '变形缝节点', '构造图集', 1),
    ('基础节点',   '基础节点',   '构造图集', 2),
    ('墙体节点',   '墙体节点',   '构造图集', 3),
    ('屋面节点',   '屋面节点',   '构造图集', 4),
    ('幕墙节点',   '幕墙节点',   '构造图集', 5),
    ('楼地面节点', '楼地面节点', '构造图集', 6),
    ('门窗节点',   '门窗节点',   '构造图集', 7);
