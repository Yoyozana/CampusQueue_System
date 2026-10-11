-- Run this ONCE on an existing CampusQueue database (made before the
-- account-lockout feature). New databases built from schema.sql already
-- have these columns.
SELECT DATABASE();
SHOW COLUMNS FROM users;
USE CampusQueue_System;

ALTER TABLE users
    ADD COLUMN failed_login_attempts INT NOT NULL DEFAULT 0,
    ADD COLUMN locked_until DATETIME NULL;
    
SHOW COLUMNS FROM users;

-- To unlock a student by hand:
-- UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE username = '220123456';
