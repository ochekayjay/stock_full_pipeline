

-- 1. One role holding the permission set
CREATE ROLE lambda_processing_role;

-- 2. Schema-level access — required before table grants mean anything
GRANT USAGE ON SCHEMA stock_pipeline TO ROLE lambda_processing_role;

-- 3. Grant on tables that exist RIGHT NOW
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stock_pipeline TO ROLE lambda_processing_role;

-- 4. The critical piece: default privileges scoped to the dbt role specifically,
--    since dbt is confirmed as the only identity that ever creates/recreates tables here
GRANT CREATE ON SCHEMA stock_pipeline TO "< Master User >";

ALTER DEFAULT PRIVILEGES FOR USER "< Master User >"
IN SCHEMA stock_pipeline
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ROLE lambda_processing_role;



-- 5. Grant the role to all three consuming identities
GRANT ROLE lambda_processing_role TO "<Extraction Function Role>";
GRANT ROLE lambda_processing_role TO "<Alert Function Role>";
GRANT ROLE lambda_processing_role TO "<Transformation Section Role>";