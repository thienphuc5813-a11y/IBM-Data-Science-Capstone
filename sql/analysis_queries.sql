-- IBM Automobile Sales Capstone: reproducible SQLite analysis
-- The pipeline writes the cleaned DataFrame to a table named automobile_sales.

-- 1. Overall coverage and period counts
SELECT MIN(Year) AS first_year, MAX(Year) AS last_year, COUNT(*) AS observations
FROM automobile_sales;

-- 2. Compare recession and non-recession conditions
SELECT Recession, COUNT(*) AS months,
       ROUND(AVG(Automobile_Sales), 2) AS avg_monthly_sales,
       ROUND(AVG(Price), 2) AS avg_price,
       ROUND(AVG(unemployment_rate), 2) AS avg_unemployment
FROM automobile_sales
GROUP BY Recession
ORDER BY Recession;

-- 3. Vehicle-type comparison
SELECT Vehicle_Type, Recession,
       ROUND(AVG(Automobile_Sales), 2) AS avg_sales
FROM automobile_sales
GROUP BY Vehicle_Type, Recession
ORDER BY Vehicle_Type, Recession;

-- 4. Annual sales trend
SELECT Year, ROUND(SUM(Automobile_Sales), 2) AS annual_sales
FROM automobile_sales
GROUP BY Year
ORDER BY Year;

-- 5. State-level totals (the source field City contains state names)
SELECT City AS State, ROUND(SUM(Automobile_Sales), 2) AS total_sales
FROM automobile_sales
GROUP BY City
ORDER BY total_sales DESC;

-- 6. Month-of-year seasonality
SELECT CAST(strftime('%m', Date) AS INTEGER) AS month_num,
       ROUND(AVG(Automobile_Sales), 2) AS avg_sales
FROM automobile_sales
GROUP BY month_num
ORDER BY month_num;
