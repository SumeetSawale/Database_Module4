from database.bplustree import BPlusTree

class Table:
    def __init__(self, name, schema, order=8, search_key=None):
        self.name = name
        self.schema = schema
        self.order = order
        self.search_key = search_key

        if self.search_key is None or self.search_key not in schema:
            raise ValueError("A valid `search_key` must be provided and exist in the schema.")

        self.data = BPlusTree(order=order)

    def validate_record(self, record):
        """
        Ensure the record contains exactly the schema's keys with correct data types.
        """
        if set(record.keys()) != set(self.schema.keys()):
            raise ValueError(f"Record keys do not match schema keys: {self.schema.keys()}")

        for key, value in record.items():
            expected_type = self.schema[key]
            if not isinstance(value, expected_type):
                raise TypeError(f"Field '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}")
        print(f"Record validated successfully: {record}")

    def insert(self, record):
        """
        Validate and insert the record using the search_key as index key.
        """
        self.validate_record(record)
        key = record[self.search_key]
        if self.data.search(key) is not None:
            raise ValueError(f"Record with key '{key}' already exists.")
        self.data.insert(key, record)
        print(f"Record with key '{key}' inserted successfully.")

    def get(self, record_id):
        """
        Return the record with the specified search_key value.
        """
        return self.data.search(record_id)

    def get_all(self):
        """
        Return all records in sorted key order.
        """
        all_records = []

        for key, value in self.data.get_all(): 
            all_records.append(value)  # We only want the values (the records)

        return all_records

    def update(self, record_id, new_record):
        """
        Overwrite record at given ID if it exists, ensuring schema validity.
        """
        if self.data.search(record_id) is None:
            raise ValueError(f"No record found with key '{record_id}' to update.")
        self.validate_record(new_record)
        if not self.data.update(record_id, new_record):
            raise RuntimeError("Update failed unexpectedly.")
        print(f"Record with key '{record_id}' updated successfully.")

    def delete(self, record_id):
        """
        Delete a record by its search_key value.
        """
        if self.data.search(record_id) is None:
            raise ValueError(f"No record found with key '{record_id}' to delete.")
        self.data.delete(record_id)
        print(f"Record with key '{record_id}' deleted successfully.")

    def range_query(self, start_value, end_value):
        """
        Return all records with keys in [start_value, end_value].
        """
        return [
            value for key, value in self.data.get_all()
            if start_value <= key <= end_value
        ]


