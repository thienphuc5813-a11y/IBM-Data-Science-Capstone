-- SpaceX Falcon 9 capstone: SQLite queries
-- Table: launches (loaded from dataset_part_2.csv)

-- 1. Overall first-stage landing success
SELECT COUNT(*) AS launches,
       SUM(Class) AS successful_landings,
       ROUND(100.0 * AVG(Class), 1) AS success_rate_pct
FROM launches;

-- 2. Launches and landing success by launch site
SELECT LaunchSite, COUNT(*) AS launches,
       SUM(Class) AS successful_landings,
       ROUND(100.0 * AVG(Class), 1) AS success_rate_pct
FROM launches
GROUP BY LaunchSite
ORDER BY success_rate_pct DESC;

-- 3. Average payload mass by landing outcome
SELECT Class, COUNT(*) AS launches,
       ROUND(AVG(PayloadMass), 1) AS average_payload_kg
FROM launches
GROUP BY Class
ORDER BY Class;

-- 4. Success rate by orbit
SELECT Orbit, COUNT(*) AS launches,
       ROUND(100.0 * AVG(Class), 1) AS success_rate_pct
FROM launches
GROUP BY Orbit
ORDER BY success_rate_pct DESC;

-- 5. Success rate by booster flight number
SELECT Flights, COUNT(*) AS launches,
       ROUND(100.0 * AVG(Class), 1) AS success_rate_pct
FROM launches
GROUP BY Flights
ORDER BY Flights;
