-- ============================================================
-- Business Listings Dashboard: Database Schema
-- Run this on your Railway MySQL instance
-- ============================================================

CREATE DATABASE IF NOT EXISTS business_dashboard
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE business_dashboard;

CREATE TABLE IF NOT EXISTS listing_master (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    business_name VARCHAR(255)  NOT NULL,
    category      VARCHAR(100)  NOT NULL,
    city          VARCHAR(100)  NOT NULL,
    address       TEXT,
    phone         VARCHAR(50)   DEFAULT NULL,
    source        VARCHAR(100)  NOT NULL,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_city     (city),
    INDEX idx_category (category),
    INDEX idx_source   (source)
);
