# Wireframes & UI Prototypes Description

# CampusQueue - Wireframe Description

## Project Overview
CampusQueue is a digital queue management system for university campuses. Students can join queues for various services, track their position in real-time, and receive notifications. Administrators can manage queues, call next students, and monitor analytics.

## UI Flow

### 1. Home Page (`home_page.png`)
**Purpose:** Landing page for all users (guests, students, and admins).

**Components:**
- **Logo/Header:** Displays "CampusQueue" branding.
- **Login/Register Buttons:b** Top-right corner for authentication.
- **Join Queue Button:** Prominent green button – primary CTA for students.
- **Queue Status Panel:** Shows active queues, people waiting, and estimated wait time (visible to all).
- **Footer:** Copyright and contact information.

**User Flow:**
- Guest → clicks Login → goes to login page.
- Guest → clicks Register → goes to registration page.
- Student (logged in) → clicks "Join Queue" → selects service type → receives ticket number → redirected to Student Dashboard.

---

### 2. Student Dashboard (`student_dashboard.png`)
**Purpose:** Personalized view for students after joining a queue.

**Components:**
- **Profile Info:** Student's name, ID, department.
- **Ticket Number:** Unique queue ticket (e.g., A-102).
- **Queue Position:** Real-time position in line.
- **Notifications:** System messages (e.g., wait time updates, service alerts).
- **Logout Button:** Ends session and returns to home page.

**User Flow:**
- Student logs in → views current ticket and position.
- System pushes notifications when position changes.
- Student can logout or wait to be served.

---

### 3. Admin Dashboard (`admin_dashboard.png`)
**Purpose:** Administrative control panel for managing queues.

**Components:**
- **All Queues:** Live list of all service queues with waiting counts.
- **Call Next Student:** Button to serve the next person in line.
- **Manage Service Points:** Grid of service points with status (Open/Closed) and edit controls.
- **Queue Analytics:** Daily statistics (students served, avg wait time, peak hours).

**User Flow:**
- Admin logs in → views all active queues.
- Clicks "Call Next Student" → system announces ticket number.
- Edits service point statuses as needed.
- Monitors analytics for operational insights.

---
