# Feature to Requirements Mapping – CampusQueue System
## Feature: User Authentication (Registration and Login)

- Functional Requirements:
  - Users must be able to register with their details (name, student ID, password)
  - Users must be able to log in using valid credentials
  - System must validate user input before registration
- Non-Functional Requirements:
  - Login process should take less than 2 seconds
  - System must securely store passwords (encryption)
  - System must ensure user data privacy and security
## Feature: Online Queue Joining

- Functional Requirements:
  - Students must be able to join a queue online
  - System must assign a queue number upon joining
  - System must store queue entries in order
- Non-Functional Requirements:
  - System should handle multiple users joining simultaneously
  - Queue joining should be completed within 2 seconds
  - System must be available at all times (high availability)
## Feature: Automatic Ticket Number Generation

- Functional Requirements:
  - System must generate unique ticket numbers automatically
  - Ticket numbers must follow a sequential order
  - System must prevent duplicate ticket numbers
- Non-Functional Requirements:
  - Ticket generation must be instantaneous
  - System must ensure accuracy and reliability
