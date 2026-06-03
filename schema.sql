-- ==========================================
-- PokeZOO MySQL/MariaDB Schema Definition
-- (Tables Only - Clean Start)
-- ==========================================

-- Drop tables if they exist to allow clean re-runs
DROP TABLE IF EXISTS pokemon_interactions;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS visitors;
DROP TABLE IF EXISTS feeding_schedules;
DROP TABLE IF EXISTS foods;
DROP TABLE IF EXISTS pokemon_keepers;
DROP TABLE IF EXISTS keepers;
DROP TABLE IF EXISTS pokemon;
DROP TABLE IF EXISTS habitats;
DROP TABLE IF EXISTS species_type;
DROP TABLE IF EXISTS pokemon_types;
DROP TABLE IF EXISTS pokemon_species;
DROP TABLE IF EXISTS users;

-- ==========================================
-- TABLES
-- ==========================================

-- 1. users
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'keeper', 'visitor') NOT NULL
);

-- 2. pokemon_species
CREATE TABLE pokemon_species (
    species_id INT AUTO_INCREMENT PRIMARY KEY,
    species_name VARCHAR(100) NOT NULL,
    rarity VARCHAR(50),
    UNIQUE(species_name, rarity)
);

-- 3. pokemon_types
CREATE TABLE pokemon_types (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE
);

-- 4. species_type (Many-to-Many)
CREATE TABLE species_type (
    species_id INT,
    type_id INT,
    PRIMARY KEY (species_id, type_id),
    FOREIGN KEY (species_id) REFERENCES pokemon_species(species_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (type_id) REFERENCES pokemon_types(type_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 5. habitats
CREATE TABLE habitats (
    habitat_id INT AUTO_INCREMENT PRIMARY KEY,
    habitat_name VARCHAR(100) NOT NULL UNIQUE,
    habitat_type VARCHAR(50),
    capacity INT NOT NULL,
    status ENUM('active', 'maintenance', 'closed') NOT NULL DEFAULT 'active'
);

-- 6. pokemon
CREATE TABLE pokemon (
    pokemon_id INT AUTO_INCREMENT PRIMARY KEY,
    species_id INT NOT NULL,
    habitat_id INT,
    nickname VARCHAR(100) UNIQUE,
    level INT DEFAULT 1,
    health_status ENUM('healthy', 'sick', 'injured', 'critical', 'quarantined') NOT NULL DEFAULT 'healthy',
    status ENUM('active', 'transferred', 'maintenance') NOT NULL DEFAULT 'active',
    entry_date DATE,
    FOREIGN KEY (species_id) REFERENCES pokemon_species(species_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (habitat_id) REFERENCES habitats(habitat_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Indexes for foreign keys
CREATE INDEX idx_pokemon_species ON pokemon(species_id);
CREATE INDEX idx_pokemon_habitat ON pokemon(habitat_id);

-- 7. keepers
CREATE TABLE keepers (
    keeper_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    shift VARCHAR(50),
    phone_number VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 8. pokemon_keepers (Many-to-Many Assignment)
CREATE TABLE pokemon_keepers (
    pokemon_id INT,
    keeper_id INT,
    assigned_since DATE,
    PRIMARY KEY (pokemon_id, keeper_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (keeper_id) REFERENCES keepers(keeper_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 9. foods
CREATE TABLE foods (
    food_id INT AUTO_INCREMENT PRIMARY KEY,
    food_name VARCHAR(100) NOT NULL,
    nutrition VARCHAR(255),
    stock INT NOT NULL DEFAULT 0
);

-- 10. feeding_schedules
CREATE TABLE feeding_schedules (
    feeding_id INT AUTO_INCREMENT PRIMARY KEY,
    pokemon_id INT NOT NULL,
    keeper_id INT NOT NULL,
    food_id INT NOT NULL,
    feeding_time DATETIME NOT NULL,
    status ENUM('scheduled', 'completed', 'missed') NOT NULL DEFAULT 'scheduled',
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (keeper_id) REFERENCES keepers(keeper_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (food_id) REFERENCES foods(food_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_feeding_pokemon ON feeding_schedules(pokemon_id);
CREATE INDEX idx_feeding_keeper ON feeding_schedules(keeper_id);
CREATE INDEX idx_feeding_food ON feeding_schedules(food_id);

-- 11. visitors
CREATE TABLE visitors (
    visitor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone_number VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 12. tickets
CREATE TABLE tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id INT NOT NULL,
    visit_date DATE NOT NULL,
    ticket_type VARCHAR(50),
    payment_method VARCHAR(50),
    purchase_date DATETIME NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    status ENUM('active', 'used', 'cancelled') NOT NULL DEFAULT 'active',
    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_ticket_visitor ON tickets(visitor_id);

-- 13. pokemon_interactions
CREATE TABLE pokemon_interactions (
    interaction_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    visitor_id INT NOT NULL,
    pokemon_id INT NOT NULL,
    interaction_type ENUM('photo', 'feeding', 'show', 'battle_event') NOT NULL,
    interaction_time DATETIME NOT NULL,
    notes TEXT,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(pokemon_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_interaction_visitor ON pokemon_interactions(visitor_id);
CREATE INDEX idx_interaction_pokemon ON pokemon_interactions(pokemon_id);

DELIMITER //
CREATE TRIGGER after_feeding_completed
AFTER UPDATE ON feeding_schedules
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE foods
        SET stock = stock - 1
        WHERE food_id = NEW.food_id;
    END IF;
END; //
DELIMITER ;


INSERT INTO users (username, password, role) VALUES 
('admin_oak', 'password123', 'admin'),
('keeper_brock', 'password123', 'keeper'),
('visitor_ash', 'password123', 'visitor');

SET @keeper_id = (SELECT user_id FROM users WHERE username = 'keeper_brock');
SET @visitor_id = (SELECT user_id FROM users WHERE username = 'visitor_ash');

INSERT INTO keepers (user_id, name, shift, phone_number) VALUES 
(@keeper_id, 'Brock', 'Morning', '555-0102');

INSERT INTO visitors (user_id, name, email, phone_number) VALUES 
(@visitor_id, 'Ash Ketchum', 'ash@pallettown.com', '555-0103');
