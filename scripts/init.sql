USE industrial_db;

-- ==========================================
-- 1. CLEANUP (The Nuclear Option)
-- ==========================================
-- We use DROP instead of TRUNCATE. 
-- TRUNCATE = "Empty the bin" (Fails if bin doesn't exist)
-- DROP = "Throw the bin away" (Works even if bin is missing, thanks to IF EXISTS)

SET FOREIGN_KEY_CHECKS = 0;

-- Remove the OLD tables (from Phase 1)
DROP TABLE IF EXISTS robots;
DROP TABLE IF EXISTS maintenance_logs;

-- Remove the NEW tables (if you ran this before)
DROP TABLE IF EXISTS sensor_logs;
DROP TABLE IF EXISTS machines;

SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 2. TABLE DEFINITIONS
-- ==========================================

-- A. The Machines (Assets)
CREATE TABLE IF NOT EXISTS machines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(50),
    type VARCHAR(50),
    install_date DATE,
    INDEX idx_model (model_name)
);

-- B. Real Sensor Data
CREATE TABLE IF NOT EXISTS sensor_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT,
    timestamp DATETIME,
    air_temp_k FLOAT,
    process_temp_k FLOAT,
    rpm INT,
    torque_nm FLOAT,
    tool_wear_min INT,
    target INT,
    failure_type VARCHAR(50),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    INDEX idx_machine_time (machine_id, timestamp),
    INDEX idx_failure (failure_type)
);

-- ==========================================
-- 3. SEED DATA
-- ==========================================
INSERT INTO machines (model_name, type, install_date) VALUES 
('Prusa MK3S+ #01', '3D Printer', '2022-01-15'),
('Prusa MK3S+ #02', '3D Printer', '2022-02-20'),
('Prusa MK3S+ #03', '3D Printer', '2022-03-10'),
('Prusa MK3S+ #04', '3D Printer', '2022-05-05'),
('Prusa MK3S+ #05', '3D Printer', '2022-08-12'),
('Prusa MK4 #01', '3D Printer', '2023-06-01'),
('Prusa MK4 #02', '3D Printer', '2023-07-15'),
('Prusa XL (5-Head)', 'Large Format Printer', '2023-11-20'),
('Prusa Mini+ #01', 'Rapid Prototyper', '2023-01-10'),
('Prusa SL1S Speed', 'Resin Printer', '2024-01-05');