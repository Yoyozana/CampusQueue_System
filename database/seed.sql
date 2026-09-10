
-- ============================================================
-- CampusQueue_System — sample seed data (v6, robust against
-- non-fresh auto-increment state)
-- ============================================================
-- WHY THIS VERSION EXISTS:
-- The previous seed.sql hardcoded numeric IDs everywhere — e.g.
-- `current_admin_id = 4`, assuming the admin account would always
-- get user_id 4. That only holds if `users` is completely empty
-- before this script runs. If you re-run seed.sql after an earlier
-- attempt (even a partially failed one) without fully resetting
-- the database, auto-increment continues from wherever it left off,
-- the admin account lands on a different user_id, and every
-- hardcoded `4` in this script now points at a row that doesn't
-- exist — which is exactly what produced:
--   Error Code: 1452. Cannot add or update a child row: a foreign
--   key constraint fails (`queues`, CONSTRAINT `queues_ibfk_2`
--   FOREIGN KEY (`current_admin_id`) REFERENCES `users` (`user_id`))
--
-- THE FIX: every foreign key value below is now looked up with a
-- subquery against a UNIQUE natural key (username, prefix, or
-- ticket_number) instead of a hardcoded number. This works no
-- matter what the actual auto-increment values turn out to be.
--
-- You should still start from a clean database before seeding —
-- run `DROP DATABASE IF EXISTS CampusQueue_System;` then re-run
-- schema.sql in full before this file — but this version can no
-- longer fail with a wrong-ID foreign key error even if you forget.
-- ============================================================

USE CampusQueue_System;

-- ---------- Users ----------
-- (No FK lookups needed here — these are the base rows everything
-- else references.)
INSERT INTO users (full_name, username, student_number, email, password_hash, role) VALUES
('Siya Mbulelo', '260000001', '260000001', '260000001@mywsu.ac.za',
 'scrypt:32768:8:1$Mfk99iFu9aulKveV$7cb03b8827c00c98d7b4d9b5efa0e0cad66a1e5ecb07c1cf887200b881109cf3c7f62a669c3a4dbbb8fba20d156a0aea48b474c24de0fddf987b3df8f3ffa5c9',
 'student'),
('Vuyo Mqulwa', '260000002', '260000002', '260000002@mywsu.ac.za',
 'scrypt:32768:8:1$Mfk99iFu9aulKveV$7cb03b8827c00c98d7b4d9b5efa0e0cad66a1e5ecb07c1cf887200b881109cf3c7f62a669c3a4dbbb8fba20d156a0aea48b474c24de0fddf987b3df8f3ffa5c9',
 'student'),
('Sima Mgqibelo', '260000003', '260000003', '260000003@mywsu.ac.za',
 'scrypt:32768:8:1$Mfk99iFu9aulKveV$7cb03b8827c00c98d7b4d9b5efa0e0cad66a1e5ecb07c1cf887200b881109cf3c7f62a669c3a4dbbb8fba20d156a0aea48b474c24de0fddf987b3df8f3ffa5c9',
 'student'),
('Admin User', 'admin', NULL, 'admin@iws.ac.za',
 'scrypt:32768:8:1$J4rndokhzQJGbxNm$93bc1505ab659f5707ea7e046ba4cb386fd206bec4e26d0c9d33f5396e9d821b9fbf3ff8c2ddd0adbbb0be676a2f9b861037a4f98d89da102a38b5bd658c2b7a',
 'admin');

-- ---------- Services ----------
INSERT INTO services (service_name, description, location) VALUES
('Registration', 'Student registration services', 'Main Administration Building'),
('Financial Aid', 'NSFAS and financial assistance', 'Student Centre'),
('Academic Advising', 'Academic support and advising', 'Faculty Building'),
('Student Accommodation', 'Accommodation assistance', 'Residence Office'),
('Student Card', 'Student card issuing and replacement', 'Campus Control, near the Music Department');

-- ---------- Queues ----------
-- service_id and current_admin_id are both looked up by natural key
-- (service_name, username) instead of hardcoded numbers.
-- current_admin_id is set on Financial Aid only, representing the
-- seeded admin having selected it as "today's queue" this session
-- (matching the seeded FIN-1 ticket already being 'called' below).
-- Every other queue is currently unstaffed (NULL) in this snapshot.
INSERT INTO queues (service_id, queue_name, prefix, status, current_admin_id) VALUES
((SELECT service_id FROM services WHERE service_name = 'Registration'),
   'Registration Queue', 'REG', 'open', NULL),
((SELECT service_id FROM services WHERE service_name = 'Financial Aid'),
   'Financial Aid Queue', 'FIN', 'open', (SELECT user_id FROM users WHERE username = 'admin')),
((SELECT service_id FROM services WHERE service_name = 'Academic Advising'),
   'Academic Advising Queue', 'ADV', 'paused', NULL),
((SELECT service_id FROM services WHERE service_name = 'Student Accommodation'),
   'Accommodation Queue', 'ACC', 'open', NULL),
((SELECT service_id FROM services WHERE service_name = 'Student Card'),
   'Student Card Queue', 'SC', 'open', NULL);

-- ---------- Queue counters ----------
-- queue_id looked up by prefix (UNIQUE), not assumed to be 1-5 in order.
INSERT INTO queue_counters (queue_id, last_number) VALUES
((SELECT queue_id FROM queues WHERE prefix = 'REG'), 3),   -- REG-1, REG-2, REG-3 already issued
((SELECT queue_id FROM queues WHERE prefix = 'FIN'), 1),   -- FIN-1 already issued
((SELECT queue_id FROM queues WHERE prefix = 'ADV'), 0),   -- no tickets yet (queue is paused)
((SELECT queue_id FROM queues WHERE prefix = 'ACC'), 0),   -- no tickets yet
((SELECT queue_id FROM queues WHERE prefix = 'SC'),  1);   -- SC-1 already issued

-- ---------- Queue tickets ----------
-- user_id looked up by username, queue_id looked up by prefix.
-- One served, one skipped (no-show), one called, two waiting.
INSERT INTO queue_tickets (user_id, queue_id, sequence_number, ticket_number, status, called_at, served_at) VALUES
((SELECT user_id FROM users WHERE username = '260000001'),
   (SELECT queue_id FROM queues WHERE prefix = 'REG'), 1, 'REG-1', 'served',
   NOW() - INTERVAL 12 MINUTE, NOW() - INTERVAL 9 MINUTE),
((SELECT user_id FROM users WHERE username = '260000002'),
   (SELECT queue_id FROM queues WHERE prefix = 'REG'), 2, 'REG-2', 'waiting',
   NULL, NULL),
((SELECT user_id FROM users WHERE username = '260000003'),
   (SELECT queue_id FROM queues WHERE prefix = 'REG'), 3, 'REG-3', 'skipped',
   NOW() - INTERVAL 5 MINUTE, NOW() - INTERVAL 4 MINUTE),   -- no-show
((SELECT user_id FROM users WHERE username = '260000003'),
   (SELECT queue_id FROM queues WHERE prefix = 'FIN'), 1, 'FIN-1', 'called',
   NOW() - INTERVAL 2 MINUTE, NULL),
((SELECT user_id FROM users WHERE username = '260000002'),
   (SELECT queue_id FROM queues WHERE prefix = 'SC'), 1, 'SC-1', 'waiting',
   NULL, NULL);

-- ---------- Service points ----------
-- Fixed desk→queue mappings — these do NOT change per session.
-- current_ticket_id looked up by ticket_number (UNIQUE per queue, and
-- in practice unique overall in this seed set).
-- Counter 2 is currently serving FIN-1 (the 'called' ticket above).
-- Counter 4 is assigned to Academic Advising so that once an admin
-- reopens that queue, Call Next is immediately available — a queue
-- being 'paused' doesn't mean its desk goes away, it just isn't
-- accepting new tickets for now.
INSERT INTO service_points (point_name, queue_id, current_ticket_id, is_active) VALUES
('Counter 1', (SELECT queue_id FROM queues WHERE prefix = 'REG'), NULL, TRUE),
('Counter 2', (SELECT queue_id FROM queues WHERE prefix = 'FIN'),
   (SELECT ticket_id FROM queue_tickets WHERE ticket_number = 'FIN-1'), TRUE),
('Counter 3', (SELECT queue_id FROM queues WHERE prefix = 'SC'), NULL, TRUE),
('Counter 4', (SELECT queue_id FROM queues WHERE prefix = 'ADV'), NULL, TRUE);

-- ---------- Notifications ----------
-- user_id looked up by username, ticket_id looked up by ticket_number.
INSERT INTO notifications (user_id, ticket_id, message, status) VALUES
((SELECT user_id FROM users WHERE username = '260000001'),
   (SELECT ticket_id FROM queue_tickets WHERE ticket_number = 'REG-1'),
   'You have been served for REG-1. Thank you!', 'read'),
((SELECT user_id FROM users WHERE username = '260000002'),
   (SELECT ticket_id FROM queue_tickets WHERE ticket_number = 'REG-2'),
   'You have successfully joined the Registration Queue. Your ticket is REG-2.', 'unread'),
((SELECT user_id FROM users WHERE username = '260000003'),
   (SELECT ticket_id FROM queue_tickets WHERE ticket_number = 'REG-3'),
   'You missed your turn for REG-3. Please rejoin the queue.', 'unread'),
((SELECT user_id FROM users WHERE username = '260000003'),
   (SELECT ticket_id FROM queue_tickets WHERE ticket_number = 'FIN-1'),
   'Your turn is approaching. Ticket FIN-1 has been called — please proceed to Counter 2.', 'unread'),
((SELECT user_id FROM users WHERE username = '260000002'),
   (SELECT ticket_id FROM queue_tickets WHERE ticket_number = 'SC-1'),
   'You have successfully joined the Student Card Queue. Your ticket is SC-1.', 'unread');

-- ---------- Admin actions ----------
-- admin_id looked up by username = 'admin'.
INSERT INTO admin_actions (admin_id, action_description)
SELECT user_id, action_description
FROM users
CROSS JOIN (
    SELECT 'Selected Financial Aid queue for this session' AS action_description
    UNION ALL SELECT 'Called FIN-1 in Financial Aid'
    UNION ALL SELECT 'Called REG-1 in Registration'
    UNION ALL SELECT 'Served REG-1 in Registration'
    UNION ALL SELECT 'Called REG-3 in Registration'
    UNION ALL SELECT 'Skipped REG-3 in Registration (no-show)'
    UNION ALL SELECT 'Paused the Academic Advising Queue'
) AS actions
WHERE users.username = 'admin';