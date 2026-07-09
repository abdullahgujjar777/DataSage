-- sql/create_readonly_role.sql

CREATE ROLE datasage_reader WITH LOGIN PASSWORD 'mylaptop12';

GRANT CONNECT ON DATABASE datasage TO datasage_reader;

GRANT USAGE ON SCHEMA public TO datasage_reader;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO datasage_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO datasage_reader;