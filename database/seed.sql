CREATE DATABASE IF NOT EXISTS pokezoo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pokezoo;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE pokemon_interactions;
TRUNCATE TABLE pokemon_health_history;
TRUNCATE TABLE tickets;
TRUNCATE TABLE visitors;
TRUNCATE TABLE feeding_schedules;
TRUNCATE TABLE foods;
TRUNCATE TABLE pokemon_keepers;
TRUNCATE TABLE keepers;
TRUNCATE TABLE pokemon;
TRUNCATE TABLE habitats;
TRUNCATE TABLE species_type;
TRUNCATE TABLE pokemon_types;
TRUNCATE TABLE pokemon_species;
TRUNCATE TABLE users;

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO users (username, password, role) VALUES
('admin_jenny',     'password123', 'admin'),
('keeper_misty',    'password123', 'keeper'),
('keeper_tracey',   'password123', 'keeper'),
('keeper_erika',    'password123', 'keeper'),
('visitor_serena',  'password123', 'visitor'),
('visitor_goh',     'password123', 'visitor'),
('visitor_lillie',  'password123', 'visitor'),
('visitor_clemont', 'password123', 'visitor');

INSERT INTO pokemon_types (type_name) VALUES
('Normal'),
('Fire'),
('Water'),
('Electric'),
('Grass'),
('Ice'),
('Fighting'),
('Poison'),
('Ground'),
('Flying'),
('Psychic'),
('Bug'),
('Rock'),
('Ghost'),
('Dragon'),
('Dark'),
('Steel'),
('Fairy');

INSERT INTO pokemon_species (species_name, rarity) VALUES
('Pikachu',     'Common'),
('Charmander',  'Common'),
('Squirtle',    'Common'),
('Bulbasaur',   'Common'),
('Eevee',       'Uncommon'),
('Jigglypuff',  'Uncommon'),
('Lucario',     'Rare'),
('Lapras',      'Rare'),
('Dragonite',   'Rare'),
('Gengar',      'Rare'),
('Snorlax',     'Uncommon'),
('Onix',        'Uncommon'),
('Vulpix',      'Uncommon'),
('Mewtwo',      'Legendary'),
('Mew',         'Mythical');

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Electric'
WHERE ps.species_name = 'Pikachu';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Fire'
WHERE ps.species_name IN ('Charmander', 'Vulpix');

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Water'
WHERE ps.species_name IN ('Squirtle', 'Lapras');

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Ice'
WHERE ps.species_name = 'Lapras';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Grass'
WHERE ps.species_name = 'Bulbasaur';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Poison'
WHERE ps.species_name = 'Bulbasaur';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Normal'
WHERE ps.species_name IN ('Eevee', 'Snorlax');

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Fairy'
WHERE ps.species_name = 'Jigglypuff';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Fighting'
WHERE ps.species_name = 'Lucario';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Steel'
WHERE ps.species_name = 'Lucario';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Dragon'
WHERE ps.species_name = 'Dragonite';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Flying'
WHERE ps.species_name = 'Dragonite';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Ghost'
WHERE ps.species_name = 'Gengar';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Poison'
WHERE ps.species_name = 'Gengar';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Rock'
WHERE ps.species_name = 'Onix';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Ground'
WHERE ps.species_name = 'Onix';

INSERT INTO species_type (species_id, type_id)
SELECT ps.species_id, pt.type_id
FROM pokemon_species ps JOIN pokemon_types pt ON pt.type_name = 'Psychic'
WHERE ps.species_name IN ('Mewtwo', 'Mew');

INSERT INTO habitats (habitat_name, habitat_type, capacity, status) VALUES
('Thunder Meadow',      'Grassland',  8, 'active'),
('Flame Ridge',         'Volcanic',   6, 'active'),
('Aqua Lagoon',         'Aquatic',    7, 'active'),
('Mystic Forest',       'Forest',     9, 'active'),
('Crystal Cave',        'Cave',       6, 'active'),
('Dragon Highlands',    'Mountain',   4, 'active'),
('Dream Sanctuary',     'Psychic Lab',3, 'maintenance'),
('Ancient Arena',       'Battle Zone',5, 'closed');

INSERT INTO keepers (user_id, name, shift, phone_number) VALUES
((SELECT user_id FROM users WHERE username = 'keeper_brock'),  'Brock',  'Morning',   '555-0102'),
((SELECT user_id FROM users WHERE username = 'keeper_misty'),  'Misty',  'Afternoon', '555-0104'),
((SELECT user_id FROM users WHERE username = 'keeper_tracey'), 'Tracey', 'Morning',   '555-0105'),
((SELECT user_id FROM users WHERE username = 'keeper_erika'),  'Erika',  'Night',     '555-0106');

INSERT INTO visitors (user_id, name, email, phone_number) VALUES
((SELECT user_id FROM users WHERE username = 'visitor_ash'),     'Ash Ketchum',   'ash@pallettown.com',      '555-0201'),
((SELECT user_id FROM users WHERE username = 'visitor_serena'),  'Serena',        'serena@kalosmail.com',    '555-0202'),
((SELECT user_id FROM users WHERE username = 'visitor_goh'),     'Goh',           'goh@vermillion.net',      '555-0203'),
((SELECT user_id FROM users WHERE username = 'visitor_lillie'),  'Lillie',        'lillie@alola.edu',        '555-0204'),
((SELECT user_id FROM users WHERE username = 'visitor_clemont'), 'Clemont',       'clemont@lumiose.tech',    '555-0205');

INSERT INTO foods (food_name, nutrition, stock) VALUES
('Oran Berry Mix',       'Balanced berry meal for common Pokemon',        50),
('Sitrus Berry Pack',    'High-energy berry pack for recovery',           35),
('Fresh Water Bowl',     'Clean hydration supply for aquatic Pokemon',    80),
('Charcoal Crunch',      'Warm mineral snack for Fire type Pokemon',      25),
('Leafy Salad',          'Fresh greens for Grass type Pokemon',           45),
('Protein Pellet',       'Protein-rich food for Fighting type Pokemon',   30),
('Mystic Mineral',       'Special mineral blend for rare Pokemon',        15),
('Moomoo Milk',          'Premium milk, currently out of stock',           0),
('Frozen Kelp',          'Cold aquatic plant food for Ice/Water Pokemon', 20),
('Honey Biscuit',        'Sweet snack for friendly Pokemon',              40);

INSERT INTO pokemon (species_id, habitat_id, nickname, health_status, status, entry_date) VALUES
((SELECT species_id FROM pokemon_species WHERE species_name = 'Pikachu'),    (SELECT habitat_id FROM habitats WHERE habitat_name = 'Thunder Meadow'),   'Sparky',    'healthy',     'active',      '2026-01-10'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Pikachu'),    (SELECT habitat_id FROM habitats WHERE habitat_name = 'Thunder Meadow'),   'Volt',      'healthy',     'active',      '2026-02-12'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Charmander'), (SELECT habitat_id FROM habitats WHERE habitat_name = 'Flame Ridge'),      'Blaze',     'healthy',     'active',      '2026-01-15'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Vulpix'),     (SELECT habitat_id FROM habitats WHERE habitat_name = 'Flame Ridge'),      'Ember',     'injured',     'active',      '2026-03-01'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Squirtle'),   (SELECT habitat_id FROM habitats WHERE habitat_name = 'Aqua Lagoon'),      'Shellby',   'healthy',     'active',      '2026-01-20'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Lapras'),     (SELECT habitat_id FROM habitats WHERE habitat_name = 'Aqua Lagoon'),      'Marina',    'healthy',     'active',      '2026-02-18'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Bulbasaur'),  (SELECT habitat_id FROM habitats WHERE habitat_name = 'Mystic Forest'),    'Sprout',    'healthy',     'active',      '2026-01-22'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Eevee'),      (SELECT habitat_id FROM habitats WHERE habitat_name = 'Mystic Forest'),    'Nova',      'sick',        'active',      '2026-02-05'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Jigglypuff'), (SELECT habitat_id FROM habitats WHERE habitat_name = 'Mystic Forest'),    'Melody',    'healthy',     'active',      '2026-03-11'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Onix'),       (SELECT habitat_id FROM habitats WHERE habitat_name = 'Crystal Cave'),     'Rocky',     'healthy',     'active',      '2026-01-28'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Gengar'),     (SELECT habitat_id FROM habitats WHERE habitat_name = 'Crystal Cave'),     'Shadow',    'quarantined', 'maintenance', '2026-02-25'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Dragonite'),  (SELECT habitat_id FROM habitats WHERE habitat_name = 'Dragon Highlands'), 'Nimbus',    'healthy',     'active',      '2026-03-05'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Lucario'),    (SELECT habitat_id FROM habitats WHERE habitat_name = 'Ancient Arena'),    'Aura',      'healthy',     'transferred', '2026-01-30'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Snorlax'),    (SELECT habitat_id FROM habitats WHERE habitat_name = 'Mystic Forest'),    'Dozer',     'healthy',     'active',      '2026-03-19'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Mewtwo'),     (SELECT habitat_id FROM habitats WHERE habitat_name = 'Dream Sanctuary'),  'Psycore',   'critical',    'maintenance', '2026-04-01'),
((SELECT species_id FROM pokemon_species WHERE species_name = 'Mew'),        (SELECT habitat_id FROM habitats WHERE habitat_name = 'Dream Sanctuary'),  'Miracle',   'healthy',     'maintenance', '2026-04-04');

INSERT INTO pokemon_keepers (pokemon_id, keeper_id, assigned_since) VALUES
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Sparky'),  (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  '2026-01-10'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Volt'),    (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  '2026-02-12'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Blaze'),   (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  '2026-01-15'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Ember'),   (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  '2026-03-01'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Shellby'), (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  '2026-01-20'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Marina'),  (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  '2026-02-18'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Sprout'),  (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  '2026-01-22'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Nova'),    (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  '2026-02-05'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Melody'),  (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  '2026-03-11'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Rocky'),   (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), '2026-01-28'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Shadow'),  (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), '2026-02-25'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Nimbus'),  (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), '2026-03-05'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Aura'),    (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  '2026-01-30'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Dozer'),   (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  '2026-03-19'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Psycore'), (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), '2026-04-01'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Miracle'), (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), '2026-04-04'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Nimbus'),  (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  '2026-03-06');

INSERT INTO feeding_schedules (pokemon_id, keeper_id, food_id, feeding_time, status) VALUES
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Sparky'),  (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  (SELECT food_id FROM foods WHERE food_name = 'Oran Berry Mix'),    '2026-06-15 08:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Volt'),    (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  (SELECT food_id FROM foods WHERE food_name = 'Sitrus Berry Pack'), '2026-06-15 09:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Blaze'),   (SELECT keeper_id FROM keepers WHERE name = 'Brock'),  (SELECT food_id FROM foods WHERE food_name = 'Charcoal Crunch'),   '2026-06-15 10:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Shellby'), (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  (SELECT food_id FROM foods WHERE food_name = 'Fresh Water Bowl'),  '2026-06-15 13:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Marina'),  (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  (SELECT food_id FROM foods WHERE food_name = 'Frozen Kelp'),       '2026-06-15 14:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Sprout'),  (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  (SELECT food_id FROM foods WHERE food_name = 'Leafy Salad'),       '2026-06-15 16:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Rocky'),   (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), (SELECT food_id FROM foods WHERE food_name = 'Mystic Mineral'),    '2026-06-15 20:00:00', 'scheduled'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Dozer'),   (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  (SELECT food_id FROM foods WHERE food_name = 'Honey Biscuit'),     '2026-06-14 18:00:00', 'completed'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Nova'),    (SELECT keeper_id FROM keepers WHERE name = 'Erika'),  (SELECT food_id FROM foods WHERE food_name = 'Sitrus Berry Pack'), '2026-06-14 09:00:00', 'completed'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Ember'),   (SELECT keeper_id FROM keepers WHERE name = 'Misty'),  (SELECT food_id FROM foods WHERE food_name = 'Charcoal Crunch'),   '2026-06-13 12:00:00', 'missed'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Shadow'),  (SELECT keeper_id FROM keepers WHERE name = 'Tracey'), (SELECT food_id FROM foods WHERE food_name = 'Mystic Mineral'),    '2026-06-13 22:00:00', 'missed');

INSERT INTO pokemon_interactions (ticket_id, pokemon_id, interaction_type, interaction_time, notes) VALUES
((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Ash Ketchum' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Sparky'), 'photo', '2026-06-15 09:10:00', 'Ash took a photo with Sparky.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Ash Ketchum' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Blaze'), 'show', '2026-06-15 10:25:00', 'Blaze performed a small flame show.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Ash Ketchum' AND t.visit_date = '2026-05-20' AND t.ticket_type = 'General Admission'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Shellby'), 'feeding', '2026-05-20 11:05:00', 'Visitor assisted keeper during feeding session.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Ash Ketchum' AND t.visit_date = '2026-05-20' AND t.ticket_type = 'General Admission'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Sprout'), 'photo', '2026-05-20 12:30:00', 'Ticket usage completed after second interaction.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Serena' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'General Admission'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Melody'), 'show', '2026-06-15 13:00:00', 'Melody sang during the visitor show.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Lillie' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Marina'), 'photo', '2026-06-15 09:30:00', 'Photo session near Aqua Lagoon.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Lillie' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Sparky'), 'photo', '2026-06-15 10:10:00', 'Second VIP interaction.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Lillie' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Blaze'), 'show', '2026-06-15 11:00:00', 'Third VIP interaction.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Lillie' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Rocky'), 'battle_event', '2026-06-15 14:20:00', 'Battle event demonstration.'),

((SELECT ticket_id FROM tickets t JOIN visitors v ON t.visitor_id = v.visitor_id WHERE v.name = 'Lillie' AND t.visit_date = '2026-06-15' AND t.ticket_type = 'VIP Pass'),
 (SELECT pokemon_id FROM pokemon WHERE nickname = 'Nimbus'), 'photo', '2026-06-15 16:45:00', 'Fifth interaction, VIP ticket marked used.' );

INSERT INTO pokemon_health_history (pokemon_id, old_health_status, new_health_status, changed_by, change_reason, changed_at) VALUES
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Sparky'), NULL, 'healthy', (SELECT user_id FROM users WHERE username = 'admin_oak'), 'Initial health intake.', '2026-01-10 08:00:00'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Ember'), 'healthy', 'injured', (SELECT user_id FROM users WHERE username = 'keeper_misty'), 'Minor tail burn during habitat adjustment.', '2026-05-12 14:30:00'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Nova'), 'healthy', 'sick', (SELECT user_id FROM users WHERE username = 'keeper_erika'), 'Reduced appetite and mild fever observed.', '2026-06-10 09:15:00'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Shadow'), 'healthy', 'quarantined', (SELECT user_id FROM users WHERE username = 'keeper_tracey'), 'Temporary quarantine after abnormal behavior.', '2026-06-11 21:40:00'),
((SELECT pokemon_id FROM pokemon WHERE nickname = 'Psycore'), 'sick', 'critical', (SELECT user_id FROM users WHERE username = 'admin_jenny'), 'Escalated for intensive observation.', '2026-06-12 10:00:00');
