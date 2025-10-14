import sqlite3
import threading
from datetime import datetime
from contextlib import contextmanager
from typing import Any, Iterable, Optional
import pymongo


class MCPDatabase:
    """
    A thread-safe database manager for SQLite.

    It uses thread-local storage to ensure that each thread gets its own
    database connection.
    """

    def __init__(self, db_name: str, db_type: str = "sqlite"):
        """
        Initializes the database manager.

        Args:
            db_name: The name of the SQLite database file.
        """
        self.db_name = db_name
        self.db_type = db_type
        self._local = threading.local()

    """
    Context manager for database connections.
    """
    @contextmanager
    def _get_cursor(self):
        # Get a connection from thread-local storage, or create one.
        # threading.local() ensures that 'conn' is unique to each thread,
        # so we don't need an explicit lock here.
        if not hasattr(self._local, "conn"):
            if self.db_type == "sqlite":
                # db_name for sqlite is the file path
                self._local.conn = sqlite3.connect(self.db_name, check_same_thread=False) 
            elif self.db_type == "mongodb":
                # db_name for mongodb is the connection string
                client = pymongo.MongoClient(self.db_name)
                self._local.conn = client.get_default_database() # Assumes db name is in URI

        if self.db_type == "sqlite":
            cursor = self._local.conn.cursor()
        else: # mongodb
            cursor = self._local.conn # For mongo, the 'cursor' is the database object
        try:
            yield cursor
        finally:
            if self.db_type == "sqlite":
                cursor.close()

    def execute_write_query(self, query: str, params: Optional[Iterable[Any]] = None):
        """Executes a write query (INSERT, UPDATE, DELETE) with parameters."""
        with self._get_cursor() as cursor:
            cursor.execute(query, params or [])
            self._local.conn.commit()

    def execute_read_query(self, query: str, params: Optional[Iterable[Any]] = None) -> list[Any]:
        """Executes a read query (SELECT) and returns all results."""
        with self._get_cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()
    
    def execute_mongo_write(self, collection_name: str, document: dict):
        """Executes a write operation on a MongoDB collection."""
        if self.db_type != "mongodb":
            raise TypeError("This method is for MongoDB only.")
        with self._get_cursor() as db:
            document["timestamp"] = datetime.now()
            print(document)
            return db[collection_name].insert_one(document)

    def create_timeseries_collection_if_not_exists(self, collection_name: str, time_field: str, meta_field: Optional[str] = None):
        """
        Ensures a time series collection exists in MongoDB. If the collection
        does not exist, it will be created with the specified options.
        """
        if self.db_type != "mongodb":
            raise TypeError("This method is for MongoDB only.")
        
        with self._get_cursor() as db:
            if collection_name not in db.list_collection_names():
                timeseries_options = {'timeField': time_field}
                if meta_field:
                    timeseries_options['metaField'] = meta_field
                db.create_collection(collection_name, timeseries=timeseries_options)
                print(f"Created MongoDB time series collection: '{collection_name}'")