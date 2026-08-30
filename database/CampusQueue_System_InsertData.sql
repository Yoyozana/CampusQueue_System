-- ============================================
-- Campus Queue System Sample Data
-- ============================================

-- Insert Users
INSERT INTO users (full_name, student_number, email, password, role)
VALUES
('John Doe', '20260001', 'john.doe@student.com', 'password123', 'student'),
('Jane Smith', '20260002', 'jane.smith@student.com', 'password123', 'student'),
('Peter Johnson', '20260003', 'peter.johnson@student.com', 'password123', 'student'),
('System Administrator', NULL, 'admin@campusqueue.com', 'password123', 'admin');


-- Insert Services
INSERT INTO services (service_name, description, location)
VALUES
('Registration', 'Student registration services', 'Main Administration Building'),
('Financial Aid', 'NSFAS and financial assistance', 'Student Centre'),
('Academic Advising', 'Academic support and advising', 'Faculty Building'),
('Student Accommodation', 'Accommodation assistance', 'Residence Office');


-- Insert Queues
INSERT INTO queues (service_id, queue_name, status)
VALUES
(1, 'Registration Queue', 'open'),
(2, 'Financial Aid Queue', 'open'),
(3, 'Academic Advising Queue', 'open'),
(4, 'Accommodation Queue', 'open');

-- Insert Queue Tickets
INSERT INTO queue_tickets
(user_id, queue_id, ticket_number, position, status)
VALUES
(1, 1, 'REG001', 1, 'waiting'),
(2, 1, 'REG002', 2, 'waiting'),
(3, 2, 'FIN001', 1, 'waiting');

-- Insert Notifications
INSERT INTO notifications (user_id, message, status)
VALUES
(1, 'You have successfully joined the Registration Queue.', 'unread'),
(2, 'Your current position in the Registration Queue is 2.', 'unread'),
(3, 'You have successfully joined the Financial Aid Queue.', 'unread');

-- Insert Admin Actions
INSERT INTO admin_actions (admin_id, action_description)
VALUES
(4, 'Opened the Registration Queue'),
(4, 'Opened the Financial Aid Queue'),
(4, 'Opened the Academic Advising Queue'),
(4, 'Opened the Accommodation Queue');


