-- =============================================
-- OntologyReady 种子数据脚本
-- 供应链 ATP 场景示例数据
-- 幂等：运行前清除旧数据
-- =============================================

BEGIN;

-- 清理旧数据
DELETE FROM ontology_actions_log;
DELETE FROM ontology_links;
DELETE FROM ontology_objects;
DELETE FROM ontology_types WHERE api_name IN (
    'Customer','Product','SalesOrder','ATPCommitment','ProductionOrder','Inventory',
    'Supplier','PurchaseOrder','Material','Warehouse','LogisticsOrder','BOM',
    'customer_places_order','order_contains_product','commitment_fulfills_order',
    'commitment_for_product','production_fulfills_commitment','production_produces_product',
    'inventory_stored_in_warehouse','inventory_for_product','supplier_supplies_material',
    'purchase_for_material','purchase_from_supplier','bom_contains_material','bom_for_product',
    'logistics_ships_order','logistics_from_warehouse','production_consumes_material',
    'ApproveCommitment','CreateSalesOrder','UpdateInventory','GenerateATP','ReleaseProductionOrder',
    'CreatePurchaseOrder','ConfirmReceipt','SplitOrder','CancelOrder','ExpediteOrder'
);

-- =============================================
-- 类型定义
-- =============================================
INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity) VALUES
('Customer',               'OBJECT', '客户',      '采购方企业实体',    '{"color":"#1890ff"}', 'ACTIVE'),
('Product',                'OBJECT', '产品',      '成品 SKU',          '{"color":"#52c41a"}', 'ACTIVE'),
('SalesOrder',             'OBJECT', '销售订单',  '客户采购订单',      '{"color":"#722ed1"}', 'ACTIVE'),
('ATPCommitment',          'OBJECT', '交期承诺',  'ATP 可用性承诺',    '{"color":"#fa8c16"}', 'ACTIVE'),
('ProductionOrder',        'OBJECT', '生产工单',  '制造执行工单',      '{"color":"#eb2f96"}', 'ACTIVE'),
('Inventory',              'OBJECT', '库存',      '库存记录',          '{"color":"#13c2c2"}', 'ACTIVE'),
('Supplier',               'OBJECT', '供应商',    '供应方企业',        '{"color":"#faad14"}', 'ACTIVE'),
('PurchaseOrder',          'OBJECT', '采购订单',  '向供应商采购',      '{"color":"#2f54eb"}', 'ACTIVE'),
('Material',               'OBJECT', '物料',      '原材料/零部件',     '{"color":"#a0d911"}', 'ACTIVE'),
('Warehouse',              'OBJECT', '仓库',      '仓储设施',          '{"color":"#f5222d"}', 'ACTIVE'),
('LogisticsOrder',         'OBJECT', '物流订单',  '发运单',            '{"color":"#722ed1"}', 'ACTIVE'),

('customer_places_order',             'LINK', '客户下单',          'Customer -> SalesOrder',       '{}', 'ACTIVE'),
('order_contains_product',            'LINK', '订单包含产品',      'SalesOrder -> Product',        '{}', 'ACTIVE'),
('commitment_fulfills_order',         'LINK', '承诺履行订单',      'ATPCommitment -> SalesOrder',  '{}', 'ACTIVE'),
('commitment_for_product',            'LINK', '承诺对应产品',      'ATPCommitment -> Product',     '{}', 'ACTIVE'),
('production_fulfills_commitment',    'LINK', '生产履行承诺',      'ProductionOrder -> ATPCommitment', '{}', 'ACTIVE'),
('production_produces_product',       'LINK', '生产产出产品',      'ProductionOrder -> Product',  '{}', 'ACTIVE'),
('inventory_stored_in_warehouse',     'LINK', '库存存放仓库',      'Inventory -> Warehouse',       '{}', 'ACTIVE'),
('inventory_for_product',             'LINK', '库存对应产品',      'Inventory -> Product',         '{}', 'ACTIVE'),
('supplier_supplies_material',        'LINK', '供应商供应物料',    'Supplier -> Material',         '{}', 'ACTIVE'),
('purchase_for_material',             'LINK', '采购物料',          'PurchaseOrder -> Material',    '{}', 'ACTIVE'),
('purchase_from_supplier',            'LINK', '采购自供应商',      'PurchaseOrder -> Supplier',    '{}', 'ACTIVE'),
('bom_contains_material',             'LINK', 'BOM 包含物料',      'BOM -> Material',              '{}', 'ACTIVE'),
('bom_for_product',                   'LINK', 'BOM 对应产品',      'BOM -> Product',               '{}', 'ACTIVE'),
('logistics_ships_order',             'LINK', '物流发运订单',      'LogisticsOrder -> SalesOrder', '{}', 'ACTIVE'),
('logistics_from_warehouse',          'LINK', '物流发货仓库',      'LogisticsOrder -> Warehouse',  '{}', 'ACTIVE'),
('production_consumes_material',      'LINK', '生产消耗物料',      'ProductionOrder -> Material',  '{}', 'ACTIVE'),

('ApproveCommitment',       'ACTION', '审批交期承诺',  '审批 ATP 承诺',           '{"parameters":[{"name":"commitment_id","type":"STRING","required":true,"description":"承诺 ID"},{"name":"approved","type":"BOOLEAN","required":true,"description":"批准或驳回"}]}', 'ACTIVE'),
('CreateSalesOrder',        'ACTION', '创建销售订单',  '创建新销售订单',          '{"parameters":[{"name":"customer_id","type":"STRING","required":true,"description":"客户 ID"},{"name":"product_id","type":"STRING","required":true,"description":"产品 ID"}]}', 'ACTIVE'),
('UpdateInventory',         'ACTION', '更新库存',      '入库/出库/盘点',          '{"parameters":[{"name":"product_id","type":"STRING","required":true,"description":"产品 ID"},{"name":"quantity","type":"NUMBER","required":true,"description":"变更数量"}]}', 'ACTIVE'),
('ReleaseProductionOrder',  'ACTION', '下达生产工单',  '工单从计划到可执行',      '{"parameters":[{"name":"order_id","type":"STRING","required":true,"description":"工单 ID"}]}', 'ACTIVE'),
('CreatePurchaseOrder',     'ACTION', '创建采购订单',  '创建新采购订单',          '{"parameters":[{"name":"supplier_id","type":"STRING","required":true,"description":"供应商 ID"},{"name":"material_id","type":"STRING","required":true,"description":"物料 ID"}]}', 'ACTIVE'),
('CancelOrder',             'ACTION', '取消订单',      '取消销售订单',            '{"parameters":[{"name":"order_id","type":"STRING","required":true,"description":"订单 ID"},{"name":"reason","type":"STRING","required":false,"description":"取消原因"}]}', 'ACTIVE');

-- =============================================
-- 对象实例
-- =============================================

-- 客户（6 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('a0000001-0001-0001-0001-000000000001', 'Customer', 'CUST-001', 'default', '{"name":"华东电子","region":"华东","industry":"电子制造","credit_level":"AAA","annual_revenue":"50亿"}'),
('a0000001-0001-0001-0001-000000000002', 'Customer', 'CUST-002', 'default', '{"name":"华南智造","region":"华南","industry":"智能制造","credit_level":"AA","annual_revenue":"30亿"}'),
('a0000001-0001-0001-0001-000000000003', 'Customer', 'CUST-003', 'default', '{"name":"北方重工","region":"华北","industry":"重工业","credit_level":"A","annual_revenue":"80亿"}'),
('a0000001-0001-0001-0001-000000000004', 'Customer', 'CUST-004', 'default', '{"name":"西南科技","region":"西南","industry":"信息技术","credit_level":"AA","annual_revenue":"20亿"}'),
('a0000001-0001-0001-0001-000000000005', 'Customer', 'CUST-005', 'default', '{"name":"中部汽车","region":"华中","industry":"汽车制造","credit_level":"AAA","annual_revenue":"100亿"}'),
('a0000001-0001-0001-0001-000000000006', 'Customer', 'CUST-006', 'default', '{"name":"长三角半导体","region":"华东","industry":"半导体","credit_level":"AA","annual_revenue":"45亿"}');

-- 产品（10 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('b0000001-0001-0001-0001-000000000001', 'Product', 'SKU-001', 'default', '{"name":"工业控制器 X1000","category":"控制器","unit_price":2800,"unit":"台","lead_time_days":14}'),
('b0000001-0001-0001-0001-000000000002', 'Product', 'SKU-002', 'default', '{"name":"伺服电机 M200","category":"电机","unit_price":4200,"unit":"台","lead_time_days":21}'),
('b0000001-0001-0001-0001-000000000003', 'Product', 'SKU-003', 'default', '{"name":"传感器模组 S50","category":"传感器","unit_price":680,"unit":"个","lead_time_days":7}'),
('b0000001-0001-0001-0001-000000000004', 'Product', 'SKU-004', 'default', '{"name":"电源模块 P300","category":"电源","unit_price":1500,"unit":"台","lead_time_days":10}'),
('b0000001-0001-0001-0001-000000000005', 'Product', 'SKU-005', 'default', '{"name":"PLC 可编程控制器","category":"控制器","unit_price":5600,"unit":"台","lead_time_days":30}'),
('b0000001-0001-0001-0001-000000000006', 'Product', 'SKU-006', 'default', '{"name":"变频器 V500","category":"驱动","unit_price":3200,"unit":"台","lead_time_days":14}'),
('b0000001-0001-0001-0001-000000000007', 'Product', 'SKU-007', 'default', '{"name":"HMI 人机界面","category":"显示","unit_price":2400,"unit":"台","lead_time_days":14}'),
('b0000001-0001-0001-0001-000000000008', 'Product', 'SKU-008', 'default', '{"name":"继电器模组 R100","category":"继电器","unit_price":180,"unit":"个","lead_time_days":5}'),
('b0000001-0001-0001-0001-000000000009', 'Product', 'SKU-009', 'default', '{"name":"通讯网关 G900","category":"通讯","unit_price":4800,"unit":"台","lead_time_days":21}'),
('b0000001-0001-0001-0001-000000000010', 'Product', 'SKU-010', 'default', '{"name":"安全继电器 SR200","category":"安全","unit_price":960,"unit":"个","lead_time_days":10}');

-- 供应商（5 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('c0000001-0001-0001-0001-000000000001', 'Supplier', 'SUPP-001', 'default', '{"name":"全球芯片供应","region":"海外","rating":"A","categories":["芯片","半导体"],"lead_time_avg_days":30}'),
('c0000001-0001-0001-0001-000000000002', 'Supplier', 'SUPP-002', 'default', '{"name":"华东精密制造","region":"华东","rating":"AA","categories":["精密件","模具"],"lead_time_avg_days":14}'),
('c0000001-0001-0001-0001-000000000003', 'Supplier', 'SUPP-003', 'default', '{"name":"深圳电子元件","region":"华南","rating":"A","categories":["电容","电阻","PCB"],"lead_time_avg_days":7}'),
('c0000001-0001-0001-0001-000000000004', 'Supplier', 'SUPP-004', 'default', '{"name":"北方钢铁集团","region":"华北","rating":"AAA","categories":["钢材","铝材"],"lead_time_avg_days":21}'),
('c0000001-0001-0001-0001-000000000005', 'Supplier', 'SUPP-005', 'default', '{"name":"成都软件外包","region":"西南","rating":"A","categories":["嵌入式软件","测试"],"lead_time_avg_days":14}');

-- 销售订单（15 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('d0000001-0001-0001-0001-000000000001', 'SalesOrder', 'SO-2024-001', 'default', '{"name":"SO-2024-001","order_date":"2024-01-15","required_date":"2024-02-15","priority":"HIGH","status":"已确认","total_amount":56000}'),
('d0000001-0001-0001-0001-000000000002', 'SalesOrder', 'SO-2024-002', 'default', '{"name":"SO-2024-002","order_date":"2024-01-20","required_date":"2024-03-01","priority":"NORMAL","status":"已确认","total_amount":84000}'),
('d0000001-0001-0001-0001-000000000003', 'SalesOrder', 'SO-2024-003', 'default', '{"name":"SO-2024-003","order_date":"2024-02-01","required_date":"2024-02-28","priority":"URGENT","status":"生产中","total_amount":126000}'),
('d0000001-0001-0001-0001-000000000004', 'SalesOrder', 'SO-2024-004', 'default', '{"name":"SO-2024-004","order_date":"2024-02-05","required_date":"2024-03-15","priority":"NORMAL","status":"已确认","total_amount":34000}'),
('d0000001-0001-0001-0001-000000000005', 'SalesOrder', 'SO-2024-005', 'default', '{"name":"SO-2024-005","order_date":"2024-02-10","required_date":"2024-03-10","priority":"HIGH","status":"已确认","total_amount":72000}'),
('d0000001-0001-0001-0001-000000000006', 'SalesOrder', 'SO-2024-006', 'default', '{"name":"SO-2024-006","order_date":"2024-02-15","required_date":"2024-03-20","priority":"NORMAL","status":"已确认","total_amount":48000}'),
('d0000001-0001-0001-0001-000000000007', 'SalesOrder', 'SO-2024-007', 'default', '{"name":"SO-2024-007","order_date":"2024-02-20","required_date":"2024-04-01","priority":"LOW","status":"已确认","total_amount":96000}'),
('d0000001-0001-0001-0001-000000000008', 'SalesOrder', 'SO-2024-008', 'default', '{"name":"SO-2024-008","order_date":"2024-03-01","required_date":"2024-03-25","priority":"URGENT","status":"已确认","total_amount":156000}'),
('d0000001-0001-0001-0001-000000000009', 'SalesOrder', 'SO-2024-009', 'default', '{"name":"SO-2024-009","order_date":"2024-03-05","required_date":"2024-04-10","priority":"NORMAL","status":"已确认","total_amount":28000}'),
('d0000001-0001-0001-0001-000000000010', 'SalesOrder', 'SO-2024-010', 'default', '{"name":"SO-2024-010","order_date":"2024-03-10","required_date":"2024-04-05","priority":"HIGH","status":"已确认","total_amount":64000}'),
('d0000001-0001-0001-0001-000000000011', 'SalesOrder', 'SO-2024-011', 'default', '{"name":"SO-2024-011","order_date":"2024-03-15","required_date":"2024-04-20","priority":"NORMAL","status":"已确认","total_amount":88000}'),
('d0000001-0001-0001-0001-000000000012', 'SalesOrder', 'SO-2024-012', 'default', '{"name":"SO-2024-012","order_date":"2024-03-20","required_date":"2024-04-15","priority":"HIGH","status":"已确认","total_amount":112000}'),
('d0000001-0001-0001-0001-000000000013', 'SalesOrder', 'SO-2024-013', 'default', '{"name":"SO-2024-013","order_date":"2024-04-01","required_date":"2024-05-01","priority":"NORMAL","status":"已确认","total_amount":42000}'),
('d0000001-0001-0001-0001-000000000014', 'SalesOrder', 'SO-2024-014', 'default', '{"name":"SO-2024-014","order_date":"2024-04-05","required_date":"2024-05-10","priority":"URGENT","status":"已确认","total_amount":198000}'),
('d0000001-0001-0001-0001-000000000015', 'SalesOrder', 'SO-2024-015', 'default', '{"name":"SO-2024-015","order_date":"2024-04-10","required_date":"2024-05-05","priority":"NORMAL","status":"已确认","total_amount":36000}');

-- 交期承诺（12 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('e0000001-0001-0001-0001-000000000001', 'ATPCommitment', 'ATP-001', 'default', '{"name":"ATP-001","committed_date":"2024-02-10","committed_qty":20,"confidence":0.95,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000002', 'ATPCommitment', 'ATP-002', 'default', '{"name":"ATP-002","committed_date":"2024-02-25","committed_qty":20,"confidence":0.90,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000003', 'ATPCommitment', 'ATP-003', 'default', '{"name":"ATP-003","committed_date":"2024-02-20","committed_qty":30,"confidence":0.85,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000004', 'ATPCommitment', 'ATP-004', 'default', '{"name":"ATP-004","committed_date":"2024-03-10","committed_qty":10,"confidence":0.95,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000005', 'ATPCommitment', 'ATP-005', 'default', '{"name":"ATP-005","committed_date":"2024-03-05","committed_qty":15,"confidence":0.90,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000006', 'ATPCommitment', 'ATP-006', 'default', '{"name":"ATP-006","committed_date":"2024-03-15","committed_qty":12,"confidence":0.80,"status":"待审批"}'),
('e0000001-0001-0001-0001-000000000007', 'ATPCommitment', 'ATP-007', 'default', '{"name":"ATP-007","committed_date":"2024-03-25","committed_qty":25,"confidence":0.95,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000008', 'ATPCommitment', 'ATP-008', 'default', '{"name":"ATP-008","committed_date":"2024-03-20","committed_qty":30,"confidence":0.85,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000009', 'ATPCommitment', 'ATP-009', 'default', '{"name":"ATP-009","committed_date":"2024-04-05","committed_qty":18,"confidence":0.90,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000010', 'ATPCommitment', 'ATP-010', 'default', '{"name":"ATP-010","committed_date":"2024-04-15","committed_qty":22,"confidence":0.95,"status":"已批准"}'),
('e0000001-0001-0001-0001-000000000011', 'ATPCommitment', 'ATP-011', 'default', '{"name":"ATP-011","committed_date":"2024-04-20","committed_qty":14,"confidence":0.80,"status":"待审批"}'),
('e0000001-0001-0001-0001-000000000012', 'ATPCommitment', 'ATP-012', 'default', '{"name":"ATP-012","committed_date":"2024-04-30","committed_qty":40,"confidence":0.90,"status":"已批准"}');

-- 仓库（3 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('f0000001-0001-0001-0001-000000000001', 'Warehouse', 'WH-001', 'default', '{"name":"华东中心仓","location":"上海","type":"成品仓","capacity_sqm":5000}'),
('f0000001-0001-0001-0001-000000000002', 'Warehouse', 'WH-002', 'default', '{"name":"华南分仓","location":"深圳","type":"成品仓","capacity_sqm":3000}'),
('f0000001-0001-0001-0001-000000000003', 'Warehouse', 'WH-003', 'default', '{"name":"原料中心仓","location":"苏州","type":"原料仓","capacity_sqm":8000}');

-- 物料（6 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('00000001-0001-0001-0001-000000000001', 'Material', 'MAT-001', 'default', '{"name":"MCU 芯片 A100","spec":"ARM Cortex-M4","unit":"片","safety_stock":500,"lead_time_days":30}'),
('00000001-0001-0001-0001-000000000002', 'Material', 'MAT-002', 'default', '{"name":"铝合金外壳","spec":"6061-T6","unit":"个","safety_stock":200,"lead_time_days":14}'),
('00000001-0001-0001-0001-000000000003', 'Material', 'MAT-003', 'default', '{"name":"PCB 主板 V2","spec":"4层板 FR4","unit":"块","safety_stock":300,"lead_time_days":21}'),
('00000001-0001-0001-0001-000000000004', 'Material', 'MAT-004', 'default', '{"name":"IGBT 功率模块","spec":"1200V/300A","unit":"个","safety_stock":100,"lead_time_days":45}'),
('00000001-0001-0001-0001-000000000005', 'Material', 'MAT-005', 'default', '{"name":"不锈钢紧固件套装","spec":"M3-M8","unit":"套","safety_stock":1000,"lead_time_days":7}'),
('00000001-0001-0001-0001-000000000006', 'Material', 'MAT-006', 'default', '{"name":"LCD 显示屏 7寸","spec":"1024x600","unit":"块","safety_stock":150,"lead_time_days":21}');

-- 生产工单（6 个）
INSERT INTO ontology_objects (id, object_type, external_id, dataset_id, properties) VALUES
('90000001-0001-0001-0001-000000000001', 'ProductionOrder', 'PO-001', 'default', '{"name":"PO-001","product":"工业控制器 X1000","qty":20,"start_date":"2024-02-01","end_date":"2024-02-10","status":"已完成"}'),
('90000001-0001-0001-0001-000000000002', 'ProductionOrder', 'PO-002', 'default', '{"name":"PO-002","product":"伺服电机 M200","qty":15,"start_date":"2024-02-10","end_date":"2024-02-28","status":"已完成"}'),
('90000001-0001-0001-0001-000000000003', 'ProductionOrder', 'PO-003', 'default', '{"name":"PO-003","product":"工业控制器 X1000","qty":30,"start_date":"2024-03-01","end_date":"2024-03-15","status":"进行中"}'),
('90000001-0001-0001-0001-000000000004', 'ProductionOrder', 'PO-004', 'default', '{"name":"PO-004","product":"变频器 V500","qty":12,"start_date":"2024-03-10","end_date":"2024-03-22","status":"进行中"}'),
('90000001-0001-0001-0001-000000000005', 'ProductionOrder', 'PO-005', 'default', '{"name":"PO-005","product":"PLC 可编程控制器","qty":25,"start_date":"2024-04-01","end_date":"2024-04-25","status":"计划中"}'),
('90000001-0001-0001-0001-000000000006', 'ProductionOrder', 'PO-006', 'default', '{"name":"PO-006","product":"通讯网关 G900","qty":40,"start_date":"2024-04-15","end_date":"2024-05-10","status":"计划中"}');

-- =============================================
-- 链接关系
-- =============================================

-- 客户 → 订单
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000001', 'd0000001-0001-0001-0001-000000000001', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000001', 'd0000001-0001-0001-0001-000000000003', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000001', 'd0000001-0001-0001-0001-000000000005', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000002', 'd0000001-0001-0001-0001-000000000002', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000002', 'd0000001-0001-0001-0001-000000000008', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000003', 'd0000001-0001-0001-0001-000000000004', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000003', 'd0000001-0001-0001-0001-000000000012', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000004', 'd0000001-0001-0001-0001-000000000006', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000005', 'd0000001-0001-0001-0001-000000000009', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000005', 'd0000001-0001-0001-0001-000000000014', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000006', 'd0000001-0001-0001-0001-000000000007', 'default', '{}', 1.0),
(gen_random_uuid(), 'customer_places_order', 'a0000001-0001-0001-0001-000000000006', 'd0000001-0001-0001-0001-000000000010', 'default', '{}', 1.0);

-- 订单 → 产品
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000001', 'b0000001-0001-0001-0001-000000000001', 'default', '{"quantity":20}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000002', 'b0000001-0001-0001-0001-000000000002', 'default', '{"quantity":20}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000003', 'b0000001-0001-0001-0001-000000000001', 'default', '{"quantity":30}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000004', 'b0000001-0001-0001-0001-000000000005', 'default', '{"quantity":5}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000005', 'b0000001-0001-0001-0001-000000000004', 'default', '{"quantity":20}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000006', 'b0000001-0001-0001-0001-000000000003', 'default', '{"quantity":50}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000007', 'b0000001-0001-0001-0001-000000000006', 'default', '{"quantity":30}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000008', 'b0000001-0001-0001-0001-000000000002', 'default', '{"quantity":30}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000010', 'b0000001-0001-0001-0001-000000000009', 'default', '{"quantity":12}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000012', 'b0000001-0001-0001-0001-000000000008', 'default', '{"quantity":200}', 1.0),
(gen_random_uuid(), 'order_contains_product', 'd0000001-0001-0001-0001-000000000014', 'b0000001-0001-0001-0001-000000000010', 'default', '{"quantity":100}', 1.0);

-- 承诺 → 订单
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000001', 'd0000001-0001-0001-0001-000000000001', 'default', '{}', 0.95),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000002', 'd0000001-0001-0001-0001-000000000002', 'default', '{}', 0.90),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000003', 'd0000001-0001-0001-0001-000000000003', 'default', '{}', 0.85),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000004', 'd0000001-0001-0001-0001-000000000005', 'default', '{}', 0.95),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000005', 'd0000001-0001-0001-0001-000000000004', 'default', '{}', 0.90),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000007', 'd0000001-0001-0001-0001-000000000008', 'default', '{}', 0.95),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000008', 'd0000001-0001-0001-0001-000000000010', 'default', '{}', 0.85),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000009', 'd0000001-0001-0001-0001-000000000011', 'default', '{}', 0.90),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000010', 'd0000001-0001-0001-0001-000000000012', 'default', '{}', 0.95),
(gen_random_uuid(), 'commitment_fulfills_order', 'e0000001-0001-0001-0001-000000000012', 'd0000001-0001-0001-0001-000000000014', 'default', '{}', 0.90);

-- 承诺 → 产品
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000001', 'b0000001-0001-0001-0001-000000000001', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000002', 'b0000001-0001-0001-0001-000000000002', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000003', 'b0000001-0001-0001-0001-000000000001', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000004', 'b0000001-0001-0001-0001-000000000004', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000005', 'b0000001-0001-0001-0001-000000000005', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000007', 'b0000001-0001-0001-0001-000000000002', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000008', 'b0000001-0001-0001-0001-000000000009', 'default', '{}', 1.0),
(gen_random_uuid(), 'commitment_for_product', 'e0000001-0001-0001-0001-000000000012', 'b0000001-0001-0001-0001-000000000010', 'default', '{}', 1.0);

-- 供应商 → 物料
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'supplier_supplies_material', 'c0000001-0001-0001-0001-000000000001', '00000001-0001-0001-0001-000000000001', 'default', '{}', 1.0),
(gen_random_uuid(), 'supplier_supplies_material', 'c0000001-0001-0001-0001-000000000001', '00000001-0001-0001-0001-000000000004', 'default', '{}', 1.0),
(gen_random_uuid(), 'supplier_supplies_material', 'c0000001-0001-0001-0001-000000000002', '00000001-0001-0001-0001-000000000002', 'default', '{}', 1.0),
(gen_random_uuid(), 'supplier_supplies_material', 'c0000001-0001-0001-0001-000000000003', '00000001-0001-0001-0001-000000000003', 'default', '{}', 1.0),
(gen_random_uuid(), 'supplier_supplies_material', 'c0000001-0001-0001-0001-000000000004', '00000001-0001-0001-0001-000000000005', 'default', '{}', 1.0),
(gen_random_uuid(), 'supplier_supplies_material', 'c0000001-0001-0001-0001-000000000005', '00000001-0001-0001-0001-000000000006', 'default', '{}', 1.0);

-- 生产工单 → 产品
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'production_produces_product', '90000001-0001-0001-0001-000000000001', 'b0000001-0001-0001-0001-000000000001', 'default', '{"qty":20}', 1.0),
(gen_random_uuid(), 'production_produces_product', '90000001-0001-0001-0001-000000000002', 'b0000001-0001-0001-0001-000000000002', 'default', '{"qty":15}', 1.0),
(gen_random_uuid(), 'production_produces_product', '90000001-0001-0001-0001-000000000003', 'b0000001-0001-0001-0001-000000000001', 'default', '{"qty":30}', 1.0),
(gen_random_uuid(), 'production_produces_product', '90000001-0001-0001-0001-000000000004', 'b0000001-0001-0001-0001-000000000006', 'default', '{"qty":12}', 1.0);

-- 生产工单 → 承诺
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'production_fulfills_commitment', '90000001-0001-0001-0001-000000000001', 'e0000001-0001-0001-0001-000000000001', 'default', '{}', 1.0),
(gen_random_uuid(), 'production_fulfills_commitment', '90000001-0001-0001-0001-000000000002', 'e0000001-0001-0001-0001-000000000002', 'default', '{}', 1.0),
(gen_random_uuid(), 'production_fulfills_commitment', '90000001-0001-0001-0001-000000000003', 'e0000001-0001-0001-0001-000000000003', 'default', '{}', 1.0);

-- 生产 → 物料
INSERT INTO ontology_links (id, link_type, source_id, target_id, dataset_id, properties, confidence) VALUES
(gen_random_uuid(), 'production_consumes_material', '90000001-0001-0001-0001-000000000001', '00000001-0001-0001-0001-000000000001', 'default', '{"qty_per_unit":1}', 1.0),
(gen_random_uuid(), 'production_consumes_material', '90000001-0001-0001-0001-000000000001', '00000001-0001-0001-0001-000000000002', 'default', '{"qty_per_unit":1}', 1.0),
(gen_random_uuid(), 'production_consumes_material', '90000001-0001-0001-0001-000000000001', '00000001-0001-0001-0001-000000000003', 'default', '{"qty_per_unit":1}', 1.0),
(gen_random_uuid(), 'production_consumes_material', '90000001-0001-0001-0001-000000000002', '00000001-0001-0001-0001-000000000002', 'default', '{"qty_per_unit":1}', 1.0),
(gen_random_uuid(), 'production_consumes_material', '90000001-0001-0001-0001-000000000004', '00000001-0001-0001-0001-000000000004', 'default', '{"qty_per_unit":2}', 1.0);

COMMIT;
