from typing import Any, List
from fastapi import FastAPI
from fastmcp import FastMCP
from databasemgr import MCPDatabase
from pydantic import BaseModel
import argparse
from fastmcp.server.openapi import RouteMap, MCPType
import uvicorn

# Create a FastAPI app instance first
app = FastAPI(title="My Custom Server", description="Serving MCP Tools and custom endpoints")

# Initialize two separate database managers
sqlite_db = MCPDatabase(db_name="mcp.db", db_type="sqlite")
mongo_db = MCPDatabase(db_name="mongodb://192.168.0.226:27017/sensor_data", db_type="mongodb")

# Now, create the MCP instance from the existing FastAPI app
mcp = FastMCP.from_fastapi(
    app=app, # Pass the app instance here
    route_maps=[
        # GET with path params → ResourceTemplates
        RouteMap(
            methods=["GET"], 
            pattern=r".*\{.*\}.*", 
            mcp_type=MCPType.RESOURCE_TEMPLATE
        ),
        # Other GETs → Resources
        RouteMap(
            methods=["GET"], 
            pattern=r".*", 
            mcp_type=MCPType.RESOURCE
        ),
        # POST to /temp-humidity is not an MCP Tool
        RouteMap(
            methods=["POST"],
            pattern=r"/temp-humidity",
            mcp_type=MCPType.EXCLUDE # Using NONE is more explicit for excluding
        ),
        # POST/PUT/DELETE → Tools (default)
    ],
)

def setup_database():
    """Create the greetings table if it doesn't exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS greetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL DEFAULT 0,
        message TEXT NOT NULL DEFAULT 'Hello',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    sqlite_db.execute_write_query(create_table_query)
    print("Database setup complete. 'greetings' table is ready.")

def setup_mongo_database():
    """Create the time series collection for sensor readings if it doesn't exist."""
    mongo_db.create_timeseries_collection_if_not_exists(
        collection_name="readings",
        time_field="timestamp",
        meta_field="metadata"
    )
    print("MongoDB setup complete. 'readings' time series collection is ready.")

class TempHumidityReading(BaseModel):
    temp: float
    humidity: float
    sensor_id: str

@app.post("/temp-humidity")
def add_temp_humidity_mongo(reading: TempHumidityReading):
    """Adds a temperature and humidity reading to MongoDB."""
    document = {
        "metadata": {"sensor_id": reading.sensor_id},
        "temp": reading.temp,
        "humidity": reading.humidity,
    }
    mongo_db.execute_mongo_write("readings", document)
    print(reading)
    return {"status": "success"}

@mcp.tool
def greet(name: str) -> str:
    """A simple tool that returns a greeting message."""
    return f"Hello, {name}!"

@mcp.tool(description="Logs a greeting including the name and age into the database.")
def log_greeting(name: str, age: int = 0, msg: str = "Hello") -> str:
    """
    Securely inserts a name and age pair nto the 'greetings' table.

    Sample Query:
        Args: 
            name: str
            age: int
            message: str
        INSERT INTO greetings (name, age, message) VALUES ('John', 40, 'Hello')
    
    Returns: 
     String indicating success or failure.
    """
    query = "INSERT INTO greetings (name, age, message) VALUES (?,?, ?)"
    params = [name, age, msg ]
    sqlite_db.execute_write_query(query, params)
    return f"Successfully logged greeting for {name} of age {age}."

@mcp.tool(description="Reads all logged greetings from the database.")
def read_greetings() -> List[Any]:
    """Reads all records from the 'greetings' table."""
    query = "SELECT id, name,age, timestamp FROM greetings ORDER BY timestamp DESC"
    return sqlite_db.execute_read_query(query)

if __name__ == "__main__":
    setup_database()
    setup_mongo_database()
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-type", type=str, default="sse",choices=["sse", "stdio"])
    args = parser.parse_args()
    if args.server_type == "stdio":
        mcp.run_stdio()
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)