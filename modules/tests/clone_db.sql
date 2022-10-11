SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'planet'
AND pid <> pg_backend_pid();
CREATE DATABASE planet_test
WITH TEMPLATE planet
OWNER postgres;