-- Runs only in the two independent rehearsal databases; creates no privileged app role.
\getenv app_password COMPANION_DB_PASSWORD
SELECT format('CREATE ROLE companion LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='companion') \gexec
GRANT CONNECT ON DATABASE :"DBNAME" TO companion;
GRANT USAGE, CREATE ON SCHEMA public TO companion;
