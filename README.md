# PokeZOO Management System

PokeZOO is a hybrid database management system built for a university final project. It simulates a Pokémon zoo ecosystem using both relational (MySQL) and non-relational (MongoDB) databases.

## Technology Stack
- **Backend:** Python FastAPI
- **Relational DB:** MySQL via `PyMySQL` driver using raw SQL queries
- **Non-Relational DB:** MongoDB via `Motor` async driver
- **Frontend:** HTML Server-Side Templates (Jinja2) and TailwindCSS via CDN
- **Authentication:** Cookie/Session-based authentication (No JWTs)

## Hybrid Database Architecture
PokeZOO leverages a hybrid approach to data storage, separating strictly structured data from unstructured documentation.

1. **MySQL (Relational)**
   Used for strict, relational data that requires referential integrity, foreign keys, and cascading updates.
   - Users & Roles
   - Habitats & Capacities
   - Pokémon (Species, Types, Stats)
   - Keepers & Assignments
   - Ticketing & Visitors
   - Foods & Feeding Schedules

2. **MongoDB (NoSQL)**
   Used for unstructured, document-heavy data that may vary in schema.
   - **Behavior Logs:** Keepers log unstructured daily behavioral observations.
   - **Incident Reports:** Keepers submit potentially complex arrays of actions and severities for emergencies.
   - **Visitor Reviews:** Visitors submit text feedback and ratings.

---

## User Roles & Capabilities

The system strictly divides access using session roles.

### 1. Admin (`admin`)
The Zoo Director. They have full structural control over the database.
- **Dashboard:** View aggregated statistics of the zoo.
- **Manage Pokémon:** Add new Pokémon to the zoo and assign them to habitats.
- **Manage Habitats:** Build new enclosures and manage capacities.
- **SQL Playground:** Execute raw SQL queries directly in the browser to analyze data dynamically (safe `DROP` prevention included).
- **MongoDB Viewer:** View raw JSON documents stored in the NoSQL collections.

### 2. Keeper (`keeper`)
The zoo workers assigned to take care of specific Pokémon.
- **Dashboard:** View their assigned Pokémon and their health status.
- **Feeding Management:** Mark scheduled feedings as completed. *(Note: This can trigger a MySQL Event/Trigger to reduce food inventory stock!)*
- **Log Behavior (MongoDB):** Submit daily observation logs regarding Pokémon mood and behavior.
- **Report Incidents (MongoDB):** Submit severe incident reports regarding specific habitats or Pokémon.

### 3. Visitor (`visitor`)
The public customers visiting the zoo.
- **Dashboard:** View active and used tickets.
- **Explore Habitats:** Browse active habitats and their current Pokémon populations.
- **Ticketing:** Purchase general admission or VIP passes.
- **Reviews (MongoDB):** Submit feedback and ratings regarding their experience at the zoo.

---

## Folder Structure

```text
pokezoo-be/
├── .env                  # Environment variables (DB credentials)
├── app/
│   ├── main.py           # Application entry point & middleware setup
│   ├── database.py       # MySQL and MongoDB connection handlers
│   ├── routes/           # Request handlers separated by role
│   │   ├── admin/        # Admin routes (pokemon, habitats, foods, species, schedules)
│   │   ├── keeper/       # Keeper routes (dashboard, feedings, MongoDB logs)
│   │   ├── visitor/      # Visitor routes (habitats, tickets, MongoDB reviews)
│   │   └── auth.py       # Login, logout, and session handling
│   ├── templates/        # HTML Jinja2 templates separated by role
│   │   ├── admin/        # Admin HTML views
│   │   ├── keeper/       # Keeper HTML views
│   │   ├── visitor/      # Visitor HTML views
│   │   ├── auth/         # Login HTML
│   │   └── base.html     # Main layout wrapper
│   └── static/           # Static assets (CSS, JS, Images)
├── database/             # Database initialization scripts
│   ├── schema.sql        # MySQL table schemas, indexes, and triggers
│   ├── seed.sql          # MySQL dummy data
│   └── mongo_seed.js     # MongoDB dummy data
└── requirements.txt      # Python dependencies
```

---

## How to Run Locally

### Prerequisites
- Python 3.8+
- MySQL / MariaDB Server running locally
- MongoDB Server running locally (`mongodb://127.0.0.1:27017`)
- `make` (for running Makefile commands)

### Installation & Setup

1. **Database Configuration**
   By default, the application connects to a MySQL database named `pokezoo` on localhost.
   You can override this by editing `app/database.py` or exporting environment variables:
   - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`

2. **Create the Database**
   Ensure MySQL and MongoDB are running, then create the `pokezoo` database in MySQL:
   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS pokezoo;"
   ```

3. **Run Full Setup (Install, Migrate, & Seed)**
   We provide a `Makefile` to automate the entire setup process. This will install Python dependencies, create tables, and insert dummy data for both MySQL and MongoDB:
   ```bash
   make setup
   ```

4. **Start the Development Server**
   ```bash
   make dev
   ```

5. **Access the Application**
   Open your browser and navigate to `http://localhost:8000`

### Dummy Accounts
If you imported `seed.sql`, you can log in using:
- **Admin**: Username: `admin_oak` | Password: `password123`
- **Keeper**: Username: `keeper_brock` | Password: `password123`
- **Visitor**: Username: `visitor_ash` | Password: `password123`

---
