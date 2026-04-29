# System Architecture Overview – Campus Queue System

## Architectural Style

**Layered Architecture**

The Campus Queue System is designed using a **Layered Architecture**, where the system is divided into three main layers, each with a specific responsibility. This structure ensures clear separation of concerns and improves maintainability.

### Layers

* **Presentation Layer**
  The user interface where students and staff interact with the system.

  * Students can join queues, view waiting times, and receive updates.
  * Staff can manage queues and call the next student.

* **Application Layer**
  Handles all business logic and system operations.

  * Processes queue requests (join, leave, prioritize)
  * Controls queue flow and rules
  * Communicates between frontend and database

* **Data Layer**
  Responsible for storing and retrieving data.

  * Stores student records, queue data, and service information
  * Ensures data consistency and persistence

---

## Alternative Options Considered

### Monolithic Architecture

* **Advantages:**

  * Easy to develop and deploy
  * Suitable for small systems

* **Disadvantages:**

  * Hard to scale as the number of users increases
  * Difficult to maintain when the system becomes complex

---

### Microservices Architecture

* **Advantages:**

  * Highly scalable and flexible
  * Different services (e.g., queue, notifications) can run independently

* **Disadvantages:**

  * Complex to design and manage
  * Requires more infrastructure and experience
  * Not suitable for a small student team project

---

## Trade-offs

The team selected **Layered Architecture** because it provides:

* **Simplicity** – Easy to understand and implement
* **Modularity** – Each layer has a clear responsibility
* **Maintainability** – Easier to update or fix parts of the system
* **Testability** – Each layer can be tested independently

### Accepted Trade-offs:

* Less scalable compared to microservices
* Possible delays due to communication between layers
* Requires discipline to keep layers properly separated

---

## Potential Architectural Issues

* **Tight Coupling Between Layers**
  If layers are not well separated, changes in one layer may affect others.

* **Performance Bottlenecks**
  Frequent communication between layers may slow down the system if not optimized.

* **Scalability Limitations**
  The system may need redesign if the number of users grows significantly.

* **Data Consistency Challenges**
  Incorrect handling of queue updates could lead to duplicate or incorrect queue positions.

---

## High-Level Architecture Diagram

```id="b0t9sk"
+-------------------------------+
|     Presentation Layer        |
| (Web/Mobile App for Students  |
|        and Staff)             |
+-------------------------------+
               |
               v
+-------------------------------+
|     Application Layer         |
| (Queue Management Logic,      |
|  Notifications, API Services) |
+-------------------------------+
               |
               v
+-------------------------------+
|         Data Layer            |
| (Database: Queue Records,     |
|  Users, Services)             |
+-------------------------------+
```

---

## Explanation of Diagram

* **Presentation Layer:**
  Provides the interface where users interact with the system. Students join queues and staff manage them.

* **Application Layer:**
  Acts as the core of the system. It processes all requests, applies queue rules, and ensures correct system behavior.

* **Data Layer:**
  Stores all system data such as queue positions, user details, and service records.

---

## Justification

The Layered Architecture is the most suitable choice for the Campus Queue System because:

* It ensures **clear separation of concerns** between interface, logic, and data
* It is **easy for a student team to implement and manage**
* It supports **future upgrades**, such as adding mobile apps or notifications
* It aligns well with common technologies like:

  * Frontend: HTML, CSS, JavaScript
  * Backend: C++ / Python / Java
  * Database: MySQL / PostgreSQL

---

## Summary

The selected architecture provides a **structured, simple, and maintainable solution** for managing campus queues. While it may not offer the scalability of microservices, it is the most practical and efficient approach for this project.


