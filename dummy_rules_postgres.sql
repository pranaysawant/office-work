-- ============================================================================
-- DUMMY EMAIL ROUTING RULES - Postgres
-- ============================================================================
-- Purpose : exercise every permutation of rule logic, operator, threshold,
--           sequence and status flag for the DB-driven routing engine.
-- Scope   : email_routing_field_code is 'SUBJECT' on every condition.
--
-- CLEANUP CONTRACT
--   Every dummy row is tagged twice, so cleanup works even if the rule_id
--   format has to change:
--     1. email_routing_rule_id starts with 'DUMMY-'
--     2. every *_created_by / *_updated_by column is 'DUMMY_PS'
--   Use Section 5 to remove everything.
--
-- BEFORE RUNNING - confirm these three things
--   1. trail_id 3610 and 3611 exist in TRAIL. If not, change them below.
--      The UI shows Trail 'PT3610', so trail_id is most likely 3610.
--   2. There is no CHECK constraint forcing rule_id into 'TRAILID-NNN' form.
--      If there is, swap the 'DUMMY-3610-0NN' ids for a reserved high band
--      such as '3610-901'..'3610-936' and clean up on created_by instead.
--   3. email_routing_rule_id column is wide enough for 15 characters.
-- ============================================================================


-- ============================================================================
-- SECTION 1 - REMOVE ANY PREVIOUS DUMMY LOAD (child tables first)
-- ============================================================================
DELETE FROM email_routing_recipient WHERE email_routing_rule_id LIKE 'DUMMY-%';
DELETE FROM email_routing_condition WHERE email_routing_rule_id LIKE 'DUMMY-%';
DELETE FROM email_routing_rule      WHERE email_routing_rule_id LIKE 'DUMMY-%';


-- ============================================================================
-- SECTION 2 - RULES
-- ============================================================================
-- email_routing_rule_match_type is populated for backward compatibility only.
-- The authoritative operator lives on each condition row.
-- ============================================================================
INSERT INTO email_routing_rule (
    email_routing_rule_id,
    email_routing_rule_name,
    email_routing_rule_description,
    trail_id,
    email_routing_rule_environment,
    email_routing_rule_logic,
    email_routing_rule_match_type,
    email_routing_rule_fuzzy_threshold,
    email_routing_rule_enabled_flag,
    email_routing_rule_status_flag,
    email_routing_rule_created_by,
    email_routing_rule_updated_by,
    email_routing_rule_create_dt,
    email_routing_rule_update_dt
) VALUES
-- ---- Core operator coverage, all PROD / trail 3610 / enabled+active ----
('DUMMY-3610-001','D01 Single Contains','ALL logic, one CONTAINS condition',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-002','D02 Two Contains ALL','ALL logic, two CONTAINS, both must hit',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-003','D03 Three Contains ALL','ALL logic, seq gaps 10/20/30',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-004','D04 Two Contains ANY','ANY logic, conditions inserted out of seq order',
 3610,'PROD','ANY','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-005','D05 Three Contains ANY','ANY logic, three CONTAINS',
 3610,'PROD','ANY','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-006','D06 Exact Single','ALL logic, one EXACT condition',
 3610,'PROD','ALL','EXACT',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-007','D07 Exact Any','ANY logic, two EXACT alternatives',
 3610,'PROD','ANY','EXACT',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-008','D08 Starts With','ALL logic, one STARTS_WITH',
 3610,'PROD','ALL','STARTS_WITH',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-009','D09 Ends With','ALL logic, one ENDS_WITH',
 3610,'PROD','ALL','ENDS_WITH',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-010','D10 Starts And Ends','ALL logic, STARTS_WITH + ENDS_WITH combined',
 3610,'PROD','ALL','STARTS_WITH',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-011','D11 Starts Or Contains','ANY logic, STARTS_WITH + CONTAINS',
 3610,'PROD','ANY','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Threshold coverage: same FUZZY value, four different thresholds ----
('DUMMY-3610-012','D12 Fuzzy Thr 60','FUZZY ESDF at a loose threshold',
 3610,'PROD','ALL','FUZZY',60,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-013','D13 Fuzzy Thr 80','FUZZY ESDF at the default threshold',
 3610,'PROD','ALL','FUZZY',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-014','D14 Fuzzy Thr 95','FUZZY phrase at a tight threshold',
 3610,'PROD','ALL','FUZZY',95,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-015','D15 Fuzzy Thr 100','FUZZY phrase demanding a perfect score',
 3610,'PROD','ALL','FUZZY',100,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-016','D16 Fuzzy Or Contains','ANY logic mixing FUZZY 85 with CONTAINS',
 3610,'PROD','ANY','FUZZY',85,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- ANY_OF and maximum operator mixing ----
('DUMMY-3610-017','D17 Any Of Single','ALL logic, one ANY_OF with pipe-delimited values',
 3610,'PROD','ALL','ANY_OF',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-018','D18 Any Of Plus Contains','ANY logic, ANY_OF + CONTAINS',
 3610,'PROD','ANY','ANY_OF',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019','D19 All Six Operators ANY','ANY logic across all six operator codes',
 3610,'PROD','ANY','CONTAINS',70,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-020','D20 Five Operators ALL','ALL logic across five operators, hard to satisfy',
 3610,'PROD','ALL','CONTAINS',70,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Recipient variations ----
('DUMMY-3610-021','D21 Three Recipients','Three recipients, mixed USER and DISTRIBUTION_LIST',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-022','D22 Overlaps D02','Deliberately overlaps D02 to prove recipient dedupe',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Threshold precedence ----
('DUMMY-3610-023','D23 Threshold Precedence','Condition threshold 40 present, rule threshold 90 must win',
 3610,'PROD','ALL','FUZZY',90,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Child-row status flag coverage ----
('DUMMY-3610-024','D24 One Condition Inactive','ALL logic, one condition I, one A',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-025','D25 All Conditions Inactive','Rule is live but every condition is I',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-026','D26 One Recipient Inactive','Two recipients, one I',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-027','D27 All Recipients Inactive','Rule matches but has nowhere to forward',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Rule-level negative cases: MUST NOT be picked up ----
('DUMMY-3610-028','D28 Disabled Flag N','enabled_flag N, status A - must not load',
 3610,'PROD','ANY','CONTAINS',80,'N','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-029','D29 Status Inactive','enabled_flag Y, status I - must not load',
 3610,'PROD','ANY','CONTAINS',80,'Y','I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-030','D30 Disabled And Inactive','enabled_flag N, status I - must not load',
 3610,'PROD','ANY','CONTAINS',80,'N','I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-031','D31 Non Prod','environment NON-PROD - must not load in a PROD run',
 3610,'NON-PROD','ANY','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Second trail: proves trail isolation and multi-rule-per-trail ----
('DUMMY-3611-032','D32 Other Trail A','trail 3611 - must not load for a trail 3610 run',
 3611,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3611-033','D33 Other Trail B','trail 3611 second rule - same trail, multiple rules',
 3611,'PROD','ANY','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),

-- ---- Edge cases ----
('DUMMY-3610-034','D34 Single Condition ANY','ANY logic with one condition behaves like ALL',
 3610,'PROD','ANY','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-035','D35 Special Characters','Value contains ** and hyphens',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-036','D36 Case Mismatch','Lowercase stored value against uppercase subject',
 3610,'PROD','ALL','CONTAINS',80,'Y','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);


-- ============================================================================
-- SECTION 3 - CONDITIONS  (email_routing_condition_id is serial, omitted)
-- ============================================================================
INSERT INTO email_routing_condition (
    email_routing_rule_id,
    email_routing_condition_seq,
    email_routing_field_code,
    email_routing_operator_code,
    email_routing_condition_value,
    email_routing_condition_threshold,
    email_routing_condition_status_flag,
    email_routing_condition_created_by,
    email_routing_condition_updated_by,
    email_routing_condition_create_dt,
    email_routing_condition_update_dt
) VALUES
-- D01
('DUMMY-3610-001',1,'SUBJECT','CONTAINS','File Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D02
('DUMMY-3610-002',1,'SUBJECT','CONTAINS','File Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-002',2,'SUBJECT','CONTAINS','HSE_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D03 : non-contiguous sequence numbers
('DUMMY-3610-003',10,'SUBJECT','CONTAINS','File',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-003',20,'SUBJECT','CONTAINS','Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-003',30,'SUBJECT','CONTAINS','HSE_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D04 : inserted seq 2 before seq 1 on purpose
('DUMMY-3610-004',2,'SUBJECT','CONTAINS','DUMMY-EMAIL',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-004',1,'SUBJECT','CONTAINS','TESTING-EMAIL',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D05
('DUMMY-3610-005',1,'SUBJECT','CONTAINS','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-005',2,'SUBJECT','CONTAINS','TESTING-EMAIL',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-005',3,'SUBJECT','CONTAINS','DUMMY-EMAIL',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D06
('DUMMY-3610-006',1,'SUBJECT','EXACT','Online Portal Hold And Release UPLOAD Notification',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D07
('DUMMY-3610-007',1,'SUBJECT','EXACT','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-007',2,'SUBJECT','EXACT','PING',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D08
('DUMMY-3610-008',1,'SUBJECT','STARTS_WITH','RE:',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D09
('DUMMY-3610-009',1,'SUBJECT','ENDS_WITH','_EHS_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D10
('DUMMY-3610-010',1,'SUBJECT','STARTS_WITH','File Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-010',2,'SUBJECT','ENDS_WITH','_HSE_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D11
('DUMMY-3610-011',1,'SUBJECT','STARTS_WITH','FW:',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-011',2,'SUBJECT','CONTAINS','ESCALATION',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D12 / D13 : identical condition, different rule thresholds
('DUMMY-3610-012',1,'SUBJECT','FUZZY','ESDF',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-013',1,'SUBJECT','FUZZY','ESDF',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D14 / D15
('DUMMY-3610-014',1,'SUBJECT','FUZZY','Shipment Manifest Confirmation',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-015',1,'SUBJECT','FUZZY','Quarterly Compliance Report',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D16
('DUMMY-3610-016',1,'SUBJECT','FUZZY','Invoice Reminder',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-016',2,'SUBJECT','CONTAINS','PAYMENT',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D17
('DUMMY-3610-017',1,'SUBJECT','ANY_OF','INVOICE|BILLING|PAYMENT',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D18
('DUMMY-3610-018',1,'SUBJECT','ANY_OF','HSE_P|EHS_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-018',2,'SUBJECT','CONTAINS','Rejected',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D19 : all six operator codes under ANY logic
('DUMMY-3610-019',1,'SUBJECT','CONTAINS','ZZ_NEVER_1',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019',2,'SUBJECT','ANY_OF','ZZ_NEVER_2|ZZ_NEVER_3',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019',3,'SUBJECT','EXACT','ZZ_NEVER_4',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019',4,'SUBJECT','STARTS_WITH','ZZ_NEVER_5',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019',5,'SUBJECT','ENDS_WITH','ZZ_NEVER_6',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019',6,'SUBJECT','FUZZY','Escalation Notice',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D20 : five operators under ALL logic (EXACT omitted, it cannot co-exist)
('DUMMY-3610-020',1,'SUBJECT','STARTS_WITH','File Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-020',2,'SUBJECT','CONTAINS','1272',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-020',3,'SUBJECT','ANY_OF','HSE_P|EHS_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-020',4,'SUBJECT','ENDS_WITH','_HSE_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-020',5,'SUBJECT','FUZZY','File Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D21
('DUMMY-3610-021',1,'SUBJECT','CONTAINS','PAYROLL',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D22 : overlaps D02 on HSE_P
('DUMMY-3610-022',1,'SUBJECT','CONTAINS','HSE_P',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D23 : condition threshold 40 is a decoy, rule threshold 90 must win
('DUMMY-3610-023',1,'SUBJECT','FUZZY','ESDF',40,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D24 : seq 2 is inactive, so only URGENT applies
('DUMMY-3610-024',1,'SUBJECT','CONTAINS','URGENT',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-024',2,'SUBJECT','CONTAINS','ZZ_NEVER_PRESENT',NULL,'I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D25 : every condition inactive
('DUMMY-3610-025',1,'SUBJECT','CONTAINS','ORPHANED',NULL,'I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-025',2,'SUBJECT','CONTAINS','ALSO-ORPHANED',NULL,'I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D26 / D27
('DUMMY-3610-026',1,'SUBJECT','CONTAINS','BENEFITS',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-027',1,'SUBJECT','CONTAINS','NOWHERE-TO-GO',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D28 / D29 / D30 / D31 : all match 'TEST', none should ever fire
('DUMMY-3610-028',1,'SUBJECT','CONTAINS','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-029',1,'SUBJECT','CONTAINS','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-030',1,'SUBJECT','CONTAINS','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-031',1,'SUBJECT','CONTAINS','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D32 / D33 : other trail
('DUMMY-3611-032',1,'SUBJECT','CONTAINS','TEST',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3611-033',1,'SUBJECT','CONTAINS','File Accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D34 / D35 / D36
('DUMMY-3610-034',1,'SUBJECT','CONTAINS','SINGLE-ANY',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-035',1,'SUBJECT','CONTAINS','Notification** - 1272',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-036',1,'SUBJECT','CONTAINS','file accepted',NULL,'A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);


-- ============================================================================
-- SECTION 4 - RECIPIENTS  (email_routing_recipient_id is serial, omitted)
-- ============================================================================
INSERT INTO email_routing_recipient (
    email_routing_rule_id,
    email_routing_recipient_seq,
    email_routing_recipient_email,
    email_routing_recipient_type_code,
    email_routing_recipient_status_flag,
    email_routing_recipient_created_by,
    email_routing_recipient_updated_by,
    email_routing_recipient_create_dt,
    email_routing_recipient_update_dt
) VALUES
('DUMMY-3610-001',1,'dummy.d01@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D02 : two recipients, one shared with D22 to prove dedupe
('DUMMY-3610-002',1,'dummy.shared@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-002',2,'dummy.d02@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-003',1,'dummy.d03@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-004',1,'dummy.d04@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-005',1,'dummy.d05@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-006',1,'dummy.d06@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-007',1,'dummy.d07@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-008',1,'dummy.d08@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-009',1,'dummy.d09@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-010',1,'dummy.d10@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-011',1,'dummy.d11@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-012',1,'dummy.d12@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-013',1,'dummy.d13@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-014',1,'dummy.d14@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-015',1,'dummy.d15@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-016',1,'dummy.d16@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-017',1,'dummy.d17@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-018',1,'dummy.d18@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-019',1,'dummy.d19@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-020',1,'dummy.d20@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D21 : three recipients, mixed types, sequenced 1/2/3
('DUMMY-3610-021',1,'dummy.d21.first@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-021',2,'dummy.d21.list@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-021',3,'dummy.d21.third@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D22 : shares dummy.shared@example.com with D02
('DUMMY-3610-022',1,'dummy.shared@example.com','DISTRIBUTION_LIST','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-022',2,'dummy.d22@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-023',1,'dummy.d23@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-024',1,'dummy.d24@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-025',1,'dummy.d25@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D26 : seq 2 recipient is inactive
('DUMMY-3610-026',1,'dummy.d26.active@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-026',2,'dummy.d26.inactive@example.com','USER','I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
-- D27 : every recipient inactive
('DUMMY-3610-027',1,'dummy.d27.gone1@example.com','USER','I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-027',2,'dummy.d27.gone2@example.com','DISTRIBUTION_LIST','I','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-028',1,'dummy.d28@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-029',1,'dummy.d29@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-030',1,'dummy.d30@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-031',1,'dummy.d31@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3611-032',1,'dummy.d32@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3611-033',1,'dummy.d33@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-034',1,'dummy.d34@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-035',1,'dummy.d35@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),
('DUMMY-3610-036',1,'dummy.d36@example.com','USER','A','DUMMY_PS','DUMMY_PS',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP);


-- ============================================================================
-- SECTION 5 - CLEANUP  (run tomorrow, child tables first)
-- ============================================================================
-- Option A - by rule id prefix
-- DELETE FROM email_routing_recipient WHERE email_routing_rule_id LIKE 'DUMMY-%';
-- DELETE FROM email_routing_condition WHERE email_routing_rule_id LIKE 'DUMMY-%';
-- DELETE FROM email_routing_rule      WHERE email_routing_rule_id LIKE 'DUMMY-%';

-- Option B - by created_by, works even if rule ids had to change format
-- DELETE FROM email_routing_recipient WHERE email_routing_recipient_created_by = 'DUMMY_PS';
-- DELETE FROM email_routing_condition WHERE email_routing_condition_created_by = 'DUMMY_PS';
-- DELETE FROM email_routing_rule      WHERE email_routing_rule_created_by      = 'DUMMY_PS';


-- ============================================================================
-- SECTION 6 - COMMON UPDATE PATTERNS
-- ============================================================================
-- Disable the whole dummy set without deleting it
-- UPDATE email_routing_rule
--    SET email_routing_rule_enabled_flag = 'N',
--        email_routing_rule_updated_by   = 'DUMMY_PS',
--        email_routing_rule_update_dt    = CURRENT_TIMESTAMP
--  WHERE email_routing_rule_id LIKE 'DUMMY-%';

-- Re-enable the whole dummy set
-- UPDATE email_routing_rule
--    SET email_routing_rule_enabled_flag = 'Y',
--        email_routing_rule_status_flag  = 'A',
--        email_routing_rule_updated_by   = 'DUMMY_PS',
--        email_routing_rule_update_dt    = CURRENT_TIMESTAMP
--  WHERE email_routing_rule_id LIKE 'DUMMY-%';

-- Move the whole dummy set between environments
-- UPDATE email_routing_rule
--    SET email_routing_rule_environment = 'NON-PROD',
--        email_routing_rule_update_dt   = CURRENT_TIMESTAMP
--  WHERE email_routing_rule_id LIKE 'DUMMY-%';

-- Change one rule's threshold
-- UPDATE email_routing_rule
--    SET email_routing_rule_fuzzy_threshold = 75,
--        email_routing_rule_update_dt       = CURRENT_TIMESTAMP
--  WHERE email_routing_rule_id = 'DUMMY-3610-013';


-- ============================================================================
-- SECTION 7 - VERIFICATION
-- ============================================================================
-- 7a. Row counts: expect 36 rules, 58 conditions, 42 recipients
SELECT 'rules' AS tbl, COUNT(*) FROM email_routing_rule      WHERE email_routing_rule_id LIKE 'DUMMY-%'
UNION ALL
SELECT 'conditions',   COUNT(*) FROM email_routing_condition WHERE email_routing_rule_id LIKE 'DUMMY-%'
UNION ALL
SELECT 'recipients',   COUNT(*) FROM email_routing_recipient WHERE email_routing_rule_id LIKE 'DUMMY-%';

-- 7b. What a PROD run on trail 3610 should actually load.
--     Expect exactly 29 rules. Excluded: D25 (no active conditions),
--     D28/D29/D30 (flags), D31 (NON-PROD), D32/D33 (trail 3611).
SELECT r.email_routing_rule_id,
       r.email_routing_rule_name,
       TRIM(r.email_routing_rule_logic)     AS logic,
       r.email_routing_rule_fuzzy_threshold AS threshold,
       COUNT(c.email_routing_condition_id)  AS active_conditions
  FROM email_routing_rule r
  LEFT JOIN email_routing_condition c
         ON c.email_routing_rule_id = r.email_routing_rule_id
        AND TRIM(c.email_routing_condition_status_flag) = 'A'
 WHERE r.email_routing_rule_id LIKE 'DUMMY-%'
   AND r.trail_id = 3610
   AND TRIM(r.email_routing_rule_environment) = 'PROD'
   AND TRIM(r.email_routing_rule_enabled_flag) = 'Y'
   AND TRIM(r.email_routing_rule_status_flag)  = 'A'
 GROUP BY 1,2,3,4
HAVING COUNT(c.email_routing_condition_id) > 0
 ORDER BY 1;

-- 7c. Full flattened view for eyeballing conditions and recipients together
SELECT r.email_routing_rule_id,
       TRIM(r.email_routing_rule_logic)  AS logic,
       r.email_routing_rule_fuzzy_threshold AS thr,
       c.email_routing_condition_seq     AS seq,
       TRIM(c.email_routing_operator_code) AS op,
       c.email_routing_condition_value   AS val,
       TRIM(c.email_routing_condition_status_flag) AS cond_flag,
       rc.email_routing_recipient_email  AS recipient,
       TRIM(rc.email_routing_recipient_status_flag) AS rcpt_flag
  FROM email_routing_rule r
  LEFT JOIN email_routing_condition c ON c.email_routing_rule_id = r.email_routing_rule_id
  LEFT JOIN email_routing_recipient rc ON rc.email_routing_rule_id = r.email_routing_rule_id
 WHERE r.email_routing_rule_id LIKE 'DUMMY-%'
 ORDER BY r.email_routing_rule_id, c.email_routing_condition_seq, rc.email_routing_recipient_seq;

-- 7d. Rules that will match but forward nothing (expect only D27)
SELECT r.email_routing_rule_id
  FROM email_routing_rule r
 WHERE r.email_routing_rule_id LIKE 'DUMMY-%'
   AND NOT EXISTS (SELECT 1 FROM email_routing_recipient rc
                    WHERE rc.email_routing_rule_id = r.email_routing_rule_id
                      AND TRIM(rc.email_routing_recipient_status_flag) = 'A');
