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

## Entity Relationship Diagram (ERD)

![ERD](/assets/ERD.png)

The PokeZOO database is designed to manage the main operations of a Pokémon zoo, including Pokémon data, habitats, keepers, visitors, tickets, feeding schedules, health records, and visitor interactions.

### Main Entities

- `users` stores login accounts and roles such as admin, keeper, and visitor.
- `visitors` stores visitor profile information and is linked to `users`.
- `keepers` stores keeper profile information and is also linked to `users`.
- `pokemon_species` stores Pokémon species data, including rarity.
- `pokemon_types` stores Pokémon type data.
- `species_type` connects species and types because one species can have multiple types.
- `habitats` stores habitat information such as name, type, capacity, and status.
- `pokemon` stores individual Pokémon data, including species, habitat, nickname, health status, and entry date.
- `pokemon_keepers` connects Pokémon and keepers because one keeper can handle many Pokémon, and one Pokémon can be handled by many keepers.
- `foods` stores food data and stock information.
- `feeding_schedules` stores Pokémon feeding schedules, including the Pokémon, keeper, food, time, and status.
- `pokemon_health_history` records changes in Pokémon health status.
- `tickets` stores visitor ticket purchases and ticket status.
- `pokemon_interactions` records interactions between visitors and Pokémon using valid tickets.

### Relationships

The ERD shows that each Pokémon belongs to one species and one habitat. A species can have multiple types through the `species_type` table. Keepers and Pokémon have a many-to-many relationship through `pokemon_keepers`.

Visitors can buy multiple tickets, and each ticket can be used to record interactions with Pokémon. Feeding schedules connect Pokémon, keepers, and food, while health history records all health status changes made by users.

This database structure keeps the PokeZOO system organized and consistent by separating data into related tables. It supports key features such as Pokémon management, habitat management, keeper assignment, feeding schedules, ticket purchases, health tracking, and visitor interactions.

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

3. **Run Full Setup (Install, Migrate, Seed, MongoSeed)**
   We provide a `Makefile` to automate the entire setup process. This will install Python dependencies, create tables, dan insert dummy data for both MySQL and MongoDB:
   - **For Linux/Mac (or Windows with WSL/Git Bash):**
     ```bash
     make setup
     ```
   - **For Windows (Command Prompt / PowerShell):**
     Double-click `setup.bat` or run:
     ```cmd
     setup.bat
     ```

4. **Start the Development Server**
   - **For Linux/Mac:**
     ```bash
     make dev
     ```
   - **For Windows:**
     Double-click `dev.bat` or run:
     ```cmd
     dev.bat
     ```
	 if `dev.bat` doesn't works, use `pdev.bat` instead:
	 ```cmd
	 pdev.bat
	 ```

5. **Access the Application**
   Open your browser and navigate to `http://localhost:8000`

### Dummy Accounts
If you imported `schema.sql`, you can log in using:
- **Admin**: Username: `admin_oak` | Password: `password123`
- **Keeper**: Username: `keeper_brock` | Password: `password123`
- **Visitor**: Username: `visitor_ash` | Password: `password123`

### Dummy Data
And if you import `seed.sql`, you can get dozens of data like `pokemons`, `pokemon_types`, `habitats`, `foods`, etc.

In addition, you can import `mongo_seed.js` to get `visitor_reviews`, `pokemon_behavior_logs`, and `incident_reports` data.

---
