// MongoDB dummy data for PokeZOO demo.
// Import after running schema.sql and seed.sql for MySQL.

db = db.getSiblingDB("pokezoo");

db.pokemon_behavior_logs.deleteMany({});
db.incident_reports.deleteMany({});
db.visitor_reviews.deleteMany({});

db.pokemon_behavior_logs.insertMany([
  {
    pokemon_id: 1,
    keeper_user_id: 3,
    date: "2026-06-15",
    time: "08:20:00",
    behavior: "Sparky responded quickly to feeding cues and interacted calmly with visitors.",
    mood: "happy",
    trigger: "Morning feeding session",
    weather: "Clear",
    enrichment_item: "Electric-safe puzzle feeder"
  },
  {
    pokemon_id: 3,
    keeper_user_id: 3,
    date: "2026-06-15",
    time: "10:45:00",
    behavior: "Blaze practiced controlled ember bursts during the keeper-supervised show.",
    mood: "calm",
    trigger: "Scheduled fire show",
    flame_intensity: "low"
  },
  {
    pokemon_id: 8,
    keeper_user_id: 6,
    date: "2026-06-15",
    time: "11:30:00",
    behavior: "Nova stayed near shaded plants and showed reduced appetite.",
    mood: "lethargic",
    trigger: "Post-health observation",
    appetite_level: "low",
    follow_up_required: true
  },
  {
    pokemon_id: 11,
    keeper_user_id: 5,
    date: "2026-06-14",
    time: "21:15:00",
    behavior: "Shadow avoided bright areas and reacted strongly to sudden sounds.",
    mood: "agitated",
    trigger: "Noise near Crystal Cave",
    quarantine_zone: "north cave enclosure"
  },
  {
    pokemon_id: 12,
    keeper_user_id: 5,
    date: "2026-06-15",
    time: "16:50:00",
    behavior: "Nimbus completed aerial movement training without signs of fatigue.",
    mood: "happy",
    trigger: "Afternoon exercise",
    flight_duration_minutes: 12
  },
  {
    pokemon_id: 6,
    keeper_user_id: 4,
    date: "2026-06-14",
    time: "14:10:00",
    behavior: "Marina floated close to the viewing area and accepted Frozen Kelp normally.",
    mood: "calm",
    trigger: "Aquatic habitat feeding",
    water_temperature: "cool"
  }
]);

db.incident_reports.insertMany([
  {
    incident_id: "INC-DEMO-001",
    keeper_user_id: 4,
    date_reported: "2026-06-13T12:20:00.000Z",
    pokemon_id: 4,
    habitat_id: 2,
    severity: "Medium",
    description: "Ember slipped near the warm stone area and showed minor tail discomfort.",
    actions_taken: ["moved to resting zone", "applied cooling treatment", "notified admin"],
    follow_up_status: "monitor for 24 hours"
  },
  {
    incident_id: "INC-DEMO-002",
    keeper_user_id: 5,
    date_reported: "2026-06-14T21:30:00.000Z",
    pokemon_id: 11,
    habitat_id: 5,
    severity: "High",
    description: "Shadow displayed abnormal behavior and startled nearby Pokemon in Crystal Cave.",
    actions_taken: ["secured cave section", "moved visitors away", "started quarantine protocol"],
    reported_area: "Crystal Cave north corridor"
  },
  {
    incident_id: "INC-DEMO-003",
    keeper_user_id: 6,
    date_reported: "2026-06-15T09:40:00.000Z",
    pokemon_id: 8,
    habitat_id: 4,
    severity: "Low",
    description: "Nova showed low appetite during morning observation.",
    actions_taken: ["recorded symptoms", "prepared lighter meal", "scheduled health recheck"],
    suspected_cause: "temporary illness"
  },
  {
    incident_id: "INC-DEMO-004",
    keeper_user_id: 3,
    date_reported: "2026-06-15T10:05:00.000Z",
    pokemon_id: null,
    habitat_id: 1,
    severity: "Low",
    description: "A fence sensor in Thunder Meadow reported intermittent signal loss.",
    actions_taken: ["checked enclosure boundary", "reset sensor", "logged maintenance request"],
    equipment_id: "TM-SENSOR-02"
  }
]);

db.visitor_reviews.insertMany([
  {
    visitor_id: 1,
    rating: 5,
    comment: "The VIP pass was worth it. Sparky and Blaze were the highlights of the visit.",
    favorite_habitat: "Thunder Meadow",
    date_submitted: "2026-06-15T17:30:00.000Z"
  },
  {
    visitor_id: 2,
    rating: 4,
    comment: "The show was fun and the habitat layout was easy to follow.",
    favorite_habitat: "Mystic Forest",
    date_submitted: "2026-06-15T18:10:00.000Z"
  },
  {
    visitor_id: 3,
    rating: 5,
    comment: "Great educational visit. I liked seeing the ticket interaction system in action.",
    favorite_habitat: "Aqua Lagoon",
    date_submitted: "2026-06-16T12:00:00.000Z"
  },
  {
    visitor_id: 4,
    rating: 3,
    comment: "Dragon Highlands was impressive, but some areas were crowded.",
    favorite_habitat: "Dragon Highlands",
    date_submitted: "2026-06-15T19:25:00.000Z"
  },
  {
    visitor_id: 5,
    rating: 4,
    comment: "Clean facilities and helpful keepers. Would visit again.",
    favorite_habitat: "Crystal Cave",
    date_submitted: "2026-06-17T09:05:00.000Z"
  }
]);

print("MongoDB seed complete:");
print("pokemon_behavior_logs:", db.pokemon_behavior_logs.countDocuments({}));
print("incident_reports:", db.incident_reports.countDocuments({}));
print("visitor_reviews:", db.visitor_reviews.countDocuments({}));
