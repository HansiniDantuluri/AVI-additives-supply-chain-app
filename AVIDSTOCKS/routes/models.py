class Material:
    """Represents a raw material in the AVIDSTOCKS inventory system."""

    def __init__(self, id, material_name, current_quantity, 
                 reorder_level, unit_of_measure, supplier_name=None):
        self.id = id
        self.material_name = material_name
        self.__current_quantity = current_quantity  # private
        self.__reorder_level = reorder_level        # private
        self.unit_of_measure = unit_of_measure
        self.supplier_name = supplier_name

    def get_current_quantity(self):
        return self.__current_quantity

    def get_reorder_level(self):
        return self.__reorder_level

    def is_low_stock(self):
        """Returns True if current quantity is at or below reorder level."""
        return self.__current_quantity <= self.__reorder_level

    def status_label(self):
        """Returns a human-readable stock status string."""
        if self.__current_quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock():
            return "Low Stock"
        else:
            return "In Stock"


class Batch:
    """Represents a production batch in AVIDSTOCKS."""

    def __init__(self, id, batch_name, product_type, production_date):
        self.id = id
        self.batch_name = batch_name
        self.product_type = product_type
        self.production_date = production_date
        self.__materials_used = []  # private list of (material_name, quantity)

    def add_material_usage(self, material_name, quantity):
        """Records a material usage entry for this batch."""
        self.__materials_used.append((material_name, quantity))

    def get_materials_used(self):
        return self.__materials_used

    def total_materials_count(self):
        """Returns how many distinct materials were used in this batch."""
        return len(self.__materials_used)