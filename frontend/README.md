# Frontend — CampusQueue (Walter Sisulu University)

The browser-side application for CampusQueue: HTML, CSS and JavaScript,
no build step. Open `index.html` to start. Every page can also be opened
on its own.

## Pages

| Role | Page | File | Script |
|---|---|---|---|
| Everyone | Welcome / login | `index.html` | `js/app.js` |
| Student | Dashboard | `pages/student-dashboard.html` | `js/student.js` |
| Student | My Queue | `pages/student-my-queue.html` | `js/student.js` |
| Student | Join Queue | `pages/student-join-queue.html` | `js/student.js` |
| Student | Notifications | `pages/student-notifications.html` | `js/student.js` |
| Student | Profile | `pages/student-profile.html` | `js/student.js` |
| Student | Help | `pages/student-help.html` | `js/student.js` |
| Admin | Choose today's queue | `pages/admin-select-queue.html` | `js/admin.js` |
| Admin | Dashboard | `pages/admin-dashboard.html` | `js/admin.js` |
| Admin | Queues | `pages/admin-queues.html` | `js/admin.js` |
| Admin | Tickets | `pages/admin-tickets.html` | `js/admin.js` |
| Admin | Users | `pages/admin-users.html` | `js/admin.js` |
| Admin | Reports | `pages/admin-reports.html` | `js/admin.js` |
| Admin | Admin Actions | `pages/admin-actions.html` | `js/admin.js` |

## Folder structure

```
frontend/
├── index.html                  Welcome / login page
├── assets/                     Images (WSU logo, campus photo, sidebar mark)
├── styles/
│   ├── variables.css           Colours, fonts, resets, headings, pop-ups (every page)
│   ├── login.css               Welcome / login page
│   ├── layout.css              Sidebar, topbar, page container (student + admin pages)
│   ├── components.css          Service cards, status pills, notification lists, empty states
│   ├── student.css             Student pages only
│   └── admin.css               Admin pages only
├── pages/                      One HTML file per page (student-*.html, admin-*.html)
├── components/
│   ├── sidebar.js              Student/admin menu (written once, used by every page) + badges
│   ├── service-cards.js        Campus service cards
│   └── toast.js                Small pop-up notice shown top-center
├── services/                   Data layer — the only place to change when the backend is ready
│   ├── state.js                Signed-in user + saved data for this browser tab, formatting helpers
│   ├── authService.js          Sign-in and role (student/admin)
│   ├── queueService.js         Campus services, tickets, queue status, audit log, reports
│   ├── notificationService.js  Each user's notifications, unread counts, mark all read
│   └── userService.js          Accounts for the admin Users page
└── js/
    ├── app.js                  Welcome / login page
    ├── student.js              All student pages (each page is picked by <body data-page>)
    └── admin.js                All admin pages
```

## How it works

- **Login:** a student number (digits only, e.g. `220123456`) opens the
  student pages; any other username (e.g. `jmokoena`) opens the admin
  pages, starting with "Which service are you managing today?".
- **Students** join a queue (one at a time) and see their ticket number,
  position and estimated wait. They're notified when they are 3rd, 2nd
  and next in line, when they're called, and when they're served or skipped.
- **Admins** call the next student, mark tickets served or skipped, and
  open, pause or close their queue. Every action appears under
  Admin Actions, and Reports are worked out from the tickets handled.
- **No built-in data:** every ticket, notification and log entry comes
  from something a user did, kept for the current browser tab. A student
  and an admin can take turns in the same tab and see each other's changes.

## Connecting the backend

Replace `signIn()` in `services/authService.js` and the functions in
`queueService.js`, `notificationService.js` and `userService.js` with
calls to the backend, keeping the same names.

Nothing in `components/`, `js/` or `pages/` needs to change.
