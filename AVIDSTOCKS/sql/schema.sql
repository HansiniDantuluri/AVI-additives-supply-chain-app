CREATE DATABASE IF NOT EXISTS `avidstocks`;
USE `avidstocks`;

-- users: stores application users and their roles
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('admin', 'staff') NOT NULL
) ENGINE=InnoDB;

-- suppliers: stores suppliers; each supplier can supply many materials and many purchase orders
CREATE TABLE `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `supplier_name` VARCHAR(100) NOT NULL,
    `contact_person` VARCHAR(100),
    `email` VARCHAR(100) NOT NULL,
    `phone` VARCHAR(20)
) ENGINE=InnoDB;

-- materials: stores inventory items; each material may reference one supplier and can appear in many batches via batch_usage and many order_items
CREATE TABLE `materials` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `material_name` VARCHAR(100) NOT NULL,
    `category` VARCHAR(50),
    `unit_of_measure` VARCHAR(10) NOT NULL,
    `current_quantity` DECIMAL(10,2) NOT NULL CHECK (`current_quantity` >= 0),
    `reorder_level` DECIMAL(10,2) NOT NULL CHECK (`reorder_level` >= 0),
    `unit_cost` DECIMAL(10,2),
    `supplier_id` INT NULL,
    `status` ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    CONSTRAINT `fk_materials_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- batches: stores production batches; each batch can use many materials through batch_usage
CREATE TABLE `batches` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `batch_name` VARCHAR(50) NOT NULL,
    `product_type` VARCHAR(100),
    `production_date` DATE NOT NULL
) ENGINE=InnoDB;

-- batch_usage: joins batches and materials; one batch can use many materials and one material can be used in many batches
CREATE TABLE `batch_usage` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `batch_id` INT NOT NULL,
    `material_id` INT NOT NULL,
    `quantity_used` DECIMAL(10,2) NOT NULL CHECK (`quantity_used` > 0),
    CONSTRAINT `fk_batch_usage_batch` FOREIGN KEY (`batch_id`) REFERENCES `batches`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_batch_usage_material` FOREIGN KEY (`material_id`) REFERENCES `materials`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- purchase_orders: stores orders placed to suppliers; each purchase order can have many order items
CREATE TABLE `purchase_orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `supplier_id` INT NOT NULL,
    `order_date` DATE NOT NULL,
    `expected_delivery` DATE,
    `status` ENUM('Pending', 'Confirmed', 'Delivered') NOT NULL DEFAULT 'Pending',
    CONSTRAINT `fk_purchase_orders_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`)
) ENGINE=InnoDB;

-- order_items: stores items on purchase orders; each order item references one material and one purchase order
CREATE TABLE `order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `po_id` INT NOT NULL,
    `material_id` INT NOT NULL,
    `quantity` DECIMAL(10,2) NOT NULL CHECK (`quantity` > 0),
    CONSTRAINT `fk_order_items_po` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_items_material` FOREIGN KEY (`material_id`) REFERENCES `materials`(`id`)
) ENGINE=InnoDB;

-- alerts: stores inventory alerts for materials; each alert belongs to one material
CREATE TABLE `alerts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `material_id` INT NOT NULL,
    `message` VARCHAR(255) NOT NULL,
    `acknowledged` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_alerts_material` FOREIGN KEY (`material_id`) REFERENCES `materials`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- audit_log: stores actions taken by users for auditing
CREATE TABLE `audit_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `action` VARCHAR(255) NOT NULL,
    `action_timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_audit_log_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;
