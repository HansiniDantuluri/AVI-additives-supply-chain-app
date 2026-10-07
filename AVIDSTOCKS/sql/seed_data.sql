USE `avidstocks`;

INSERT INTO `users` (`username`, `password_hash`, `role`) VALUES
    ('admin', '$2b$12$y/ehUA8vfmOQ9tKa0cCrh.81vkXppNA.laR8A10pdL8iZ0dlsfh0y', 'admin'),
    ('storemanager', '$2b$12$y/ehUA8vfmOQ9tKa0cCrh.81vkXppNA.laR8A10pdL8iZ0dlsfh0y', 'staff');

INSERT INTO `suppliers` (`supplier_name`, `contact_person`, `email`, `phone`) VALUES
    ('A.S. Industries Chemicals Pvt. Ltd.', 'Amit Shah', 'procurement@asindustrieschem.com', '+91 98765 11234'),
    ('Hyderabad Pigments & Minerals Pvt. Ltd.', 'Ravi Kumar', 'sales@hydpigments.in', '+91 98480 22345'),
    ('Tanvi Specialty Additives LLP', 'Neha Patel', 'orders@tanviadditives.com', '+91 98111 33456');

INSERT INTO `materials` (`material_name`, `category`, `unit_of_measure`, `current_quantity`, `reorder_level`, `unit_cost`, `supplier_id`, `status`) VALUES
    ('Titanium Dioxide R-507', 'White Pigment', 'kg', 180.00, 75.00, 285.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'A.S. Industries Chemicals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Carbon Black 330', 'Black Pigment', 'kg', 42.00, 50.00, 145.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Yellow Pigment YL-162', 'Colour Pigment', 'kg', 120.00, 60.00, 340.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Barium Sulphate BASO4', 'Filler', 'kg', 250.00, 100.00, 40.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'A.S. Industries Chemicals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Optical Brightener OB1', 'Brightener', 'kg', 40.00, 40.00, 520.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1), 'active'),
    ('Processing Wax', 'Additive', 'kg', 140.00, 50.00, 180.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1), 'active'),
    ('Orange Pigment OR-1475', 'Colour Pigment', 'kg', 25.00, 40.00, 390.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Green Pigment GREEN-19104', 'Colour Pigment', 'kg', 0.00, 20.00, 370.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), 'inactive'),
    ('Red Pigment PR-57', 'Colour Pigment', 'kg', 95.00, 50.00, 360.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Blue Pigment PB-15', 'Colour Pigment', 'kg', 110.00, 50.00, 375.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Calcium Carbonate', 'Filler', 'kg', 300.00, 150.00, 18.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'A.S. Industries Chemicals Pvt. Ltd.' LIMIT 1), 'active'),
    ('Zinc Stearate', 'Processing Additive', 'kg', 80.00, 30.00, 210.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1), 'active'),
    ('UV Stabilizer', 'Specialty Additive', 'kg', 18.00, 25.00, 620.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1), 'active'),
    ('PE Wax', 'Processing Additive', 'kg', 90.00, 40.00, 170.00, (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1), 'active');

INSERT INTO `batches` (`batch_name`, `product_type`, `production_date`) VALUES
    ('Batch-2026-001', 'White Masterbatch', '2026-05-15'),
    ('Batch-2026-002', 'Black Masterbatch', '2026-06-01'),
    ('Batch-2026-003', 'Yellow Masterbatch', '2026-06-14');

INSERT INTO `batch_usage` (`batch_id`, `material_id`, `quantity_used`) VALUES
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-001' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Titanium Dioxide R-507' LIMIT 1), 40.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-001' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Barium Sulphate BASO4' LIMIT 1), 25.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-001' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Processing Wax' LIMIT 1), 5.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-001' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Optical Brightener OB1' LIMIT 1), 3.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-002' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Carbon Black 330' LIMIT 1), 30.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-002' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Calcium Carbonate' LIMIT 1), 15.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-002' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'PE Wax' LIMIT 1), 5.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-002' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Zinc Stearate' LIMIT 1), 3.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-003' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Yellow Pigment YL-162' LIMIT 1), 20.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-003' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Titanium Dioxide R-507' LIMIT 1), 10.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-003' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Processing Wax' LIMIT 1), 5.00),
    ((SELECT `id` FROM `batches` WHERE `batch_name` = 'Batch-2026-003' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'UV Stabilizer' LIMIT 1), 2.00);

INSERT INTO `purchase_orders` (`supplier_id`, `order_date`, `expected_delivery`, `status`) VALUES
    ((SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1), '2026-06-15', '2026-06-22', 'Pending'),
    ((SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1), '2026-06-15', '2026-06-25', 'Pending');

INSERT INTO `order_items` (`po_id`, `material_id`, `quantity`) VALUES
    ((SELECT `id` FROM `purchase_orders` WHERE `supplier_id` = (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1) AND `order_date` = '2026-06-15' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Carbon Black 330' LIMIT 1), 200.00),
    ((SELECT `id` FROM `purchase_orders` WHERE `supplier_id` = (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Hyderabad Pigments & Minerals Pvt. Ltd.' LIMIT 1) AND `order_date` = '2026-06-15' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'Orange Pigment OR-1475' LIMIT 1), 100.00),
    ((SELECT `id` FROM `purchase_orders` WHERE `supplier_id` = (SELECT `id` FROM `suppliers` WHERE `supplier_name` = 'Tanvi Specialty Additives LLP' LIMIT 1) AND `order_date` = '2026-06-15' LIMIT 1), (SELECT `id` FROM `materials` WHERE `material_name` = 'UV Stabilizer' LIMIT 1), 50.00);
