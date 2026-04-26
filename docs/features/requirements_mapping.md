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

## Feature: Real-Time Queue Position Tracking

- Functional Requirements:
  - System must display the current queue number being served
  - System must update queue position in real time
  - Students must be able to view their position in the queue

- Non-Functional Requirements:
  - Updates must reflect within 1 second
  - System must handle real-time data efficiently
  - System must be reliable with minimal downtime
## Feature: Service Selection (Registration, Finance, Administration)

- Functional Requirements:
  - Students must be able to select a service before joining the queue
  - System must create separate queues for each service
  - System must assign queue numbers based on selected service

- Non-Functional Requirements:
  - Service selection interface must be user-friendly
  - System must support multiple service queues simultaneously
  - System should respond quickly to user input
