INSERT INTO services (service_name, description, location)
VALUES
('Registration', 'Student registration services', 'Main Administration Building'),

('Financial Aid', 'NSFAS and financial assistance', 'Student Centre'),

('Academic Advising', 'Academic support and advising', 'Faculty Building'),

('Student Accommodation', 'Accommodation assistance', 'Residence Office');



INSERT INTO queues (service_id, queue_name, status)
VALUES
(1, 'Registration Queue', 'open'),

(2, 'Financial Aid Queue', 'open'),

(3, 'Academic Advising Queue', 'open'),

(4, 'Accommodation Queue', 'open');
