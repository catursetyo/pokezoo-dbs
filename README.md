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
├── schema.sql            # MySQL table schemas, indexes, and triggers
└── requirements.txt      # Python dependencies
```

---

## How to Run Locally

### Prerequisites
- Python 3.8+
- MySQL / MariaDB Server running locally
- MongoDB Server running locally (`mongodb://127.0.0.1:27017`)

### Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Configuration**
   By default, the application connects to a MySQL database named `pokezoo` on localhost.
   You can override this by editing `app/database.py` or exporting environment variables:
   - `MYSQL_HOST`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DB`

3. **Database Setup**
   - Create a database in your MySQL server named `pokezoo`.
   - Import the `schema.sql` file into that database to create all tables and triggers.
   - Example using the MySQL CLI:
     ```bash
     mysql -u your_username -p pokezoo < schema.sql
     ```
   - Or inside the MySQL prompt:
     ```sql
     CREATE DATABASE IF NOT EXISTS pokezoo;
     USE pokezoo;
     SOURCE /home/Satyz/study/sbd/fp/pokezoo-dbs/schema.sql;
     ```
   - **Important:** `schema.sql` starts with several `DROP TABLE IF EXISTS` statements, so re-importing it will reset the existing schema and data.

4. **Import Dummy Data**
   - Import `seed.sql` after `schema.sql` if you want sample data for testing and demo purposes.
   - Example using the MySQL CLI:
     ```bash
     mysql -u your_username -p pokezoo < seed.sql
     ```
   - Or inside the MySQL prompt:
     ```sql
     USE pokezoo;
     SOURCE /home/Satyz/study/sbd/fp/pokezoo-dbs/seed.sql;
     ```
   - **Important:** `seed.sql` uses multiple `TRUNCATE TABLE` statements before inserting dummy data, so re-importing it will clear existing table contents and replace them with sample data.
   - This file includes sample users, Pokemon, habitats, foods, schedules, and other demo records.

5. **Start the Server**
   ```bash
   uvicorn app.main:app --reload
   ```
   or
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   if it doesn't work, start the server inside `python venv`

6. **Access the Application**
   Open your browser and navigate to `http://localhost:8000`

### Dummy Accounts
If you imported `seed.sql`, you can log in using:
- **Admin**: Username: `admin_oak` | Password: `password123`
- **Keeper**: Username: `keeper_brock` | Password: `password123`
- **Visitor**: Username: `visitor_ash` | Password: `password123`

---
