import pickle
import os
from database.table import Table


class DatabaseManager:
    def __init__(self, filepath="db_store.pkl"):
        self.filepath = filepath
        self.databases = {}
        self.load()  # Load existing DBs if file exists

    def save(self):
        with open(self.filepath, 'wb') as f:
            pickle.dump(self.databases, f)

    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'rb') as f:
                self.databases = pickle.load(f)

    def create_database(self, db_name):
        if db_name in self.databases:
            raise ValueError(f"Database '{db_name}' already exists.")
        self.databases[db_name] = {}
        self.save()
        print(f"Database '{db_name}' created successfully.")

    def delete_database(self, db_name):
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' does not exist.")
        del self.databases[db_name]
        self.save()
        print(f"Database '{db_name}' deleted successfully.")

    def list_databases(self):
        return list(self.databases.keys())

    def create_table(self, db_name, table_name, schema, order=8, search_key=None):
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' does not exist.")
        if table_name in self.databases[db_name]:
            raise ValueError(f"Table '{table_name}' already exists in database '{db_name}'.")
        self.databases[db_name][table_name] = Table(table_name, schema, order, search_key,save_callback=self.save)
        self.save()
        print(f"Table '{table_name}' created successfully in database '{db_name}'.")

    def delete_table(self, db_name, table_name):
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' does not exist.")
        if table_name not in self.databases[db_name]:
            raise ValueError(f"Table '{table_name}' does not exist in database '{db_name}'.")
        del self.databases[db_name][table_name]
        self.save()
        print(f"Table '{table_name}' deleted successfully from database '{db_name}'.")

    def list_tables(self, db_name):
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' does not exist.")
        return list(self.databases[db_name].keys())

    def get_table(self, db_name, table_name):
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' does not exist.")
        if table_name not in self.databases[db_name]:
            raise ValueError(f"Table '{table_name}' does not exist in database '{db_name}'.")
        return self.databases[db_name][table_name]

