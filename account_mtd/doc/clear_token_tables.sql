-- Sometimes it's necessary to change the VAT number, user and password for sign-in to the API
-- This is particularly the case when developing (lets hope it's not the case for users)
-- When you do this you need to clear the cached auth data.
-- It would be better if we stored the VAT number against that auth data
-- and used that in searches so it automatically ignores dead auth data.
-- But for now, please run this SQL script when you need to do this during development.

-- e.g. docker-compose exec -T -u root postgresql psql -U odoo DBNAME < account_mtd/clear_token_tables.sql

delete from mtd_api_tokens;

delete from mtd_api_request_tracker;
