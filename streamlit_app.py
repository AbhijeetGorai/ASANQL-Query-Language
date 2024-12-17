import json
import re
import streamlit as st

# Function to load the database from a JSON file
def load_database(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to save the database to a JSON file
def save_database(file_path, databases):
    with open(file_path, 'w') as file:
        json.dump(databases, file, indent=4)

# Load the database from the JSON file
database_file_path = 'database.json'
databases = load_database(database_file_path)

def update_field_value(database_name, table_name, keyvalue_pair, change_field, change_to):
    # Locate the table in the specified database
    db_data = databases.get("databases", {}).get(database_name, {})
    table_data = db_data.get(table_name, None)
    if not table_data:
        return f"Table {table_name} not found in database {database_name}."

    # Track if any updates are made
    updated = False

    # Iterate over the rows in the table
    for row in table_data:
        # Check if all key-value conditions are satisfied
        if all(row.get(k) == v for k, v in keyvalue_pair.items()):
            # Update the specified field
            if change_field in row:
                row[change_field] = change_to
                updated = True
            else:
                return f"Field '{change_field}' not found in row: {row}"

    if updated:
        save_database(database_file_path, databases)
        return f"Table updated successfully. Updated database structure:\n{json.dumps(databases['databases'][database_name], indent=4)}"
    else:
        return "No rows matched the condition, table not updated."

def update_table_name(database_name, table_name, change_to_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            db[change_to_name] = db.pop(table_name)
            save_database(database_file_path, databases)
            return f"Table name changed from '{table_name}' to '{change_to_name}' in database '{database_name}'.\nUpdated database structure:\n{json.dumps(databases['databases'][database_name], indent=4)}"
        else:
            return f"Table '{table_name}' not found in database '{database_name}'."
    else:
        return f"Database '{database_name}' not found."

def update_field_name(database_name, table_name, field_name, change_to_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            table = db[table_name]
            for row in table:
                if field_name in row:
                    row[change_to_name] = row.pop(field_name)
            save_database(database_file_path, databases)
            return f"Field name changed from '{field_name}' to '{change_to_name}' in table '{table_name}' within database '{database_name}'.\nUpdated database structure:\n{json.dumps(databases['databases'][database_name], indent=4)}"
        else:
            return f"Table '{table_name}' not found in database '{database_name}'."
    else:
        return f"Database '{database_name}' not found."

def update_table(database_name, table_name, keyvalue_pair, change_field, change_to):
    return update_field_value(database_name, table_name, keyvalue_pair, change_field, change_to)

def change_table_name(database_name, table_name, change_name_to):
    return update_table_name(database_name, table_name, change_name_to)

def change_field_name(database_name, table_name, field_name, change_field_name_to):
    return update_field_name(database_name, table_name, field_name, change_field_name_to)

def parse_update_query(query):
    # Extract the database name
    database_match = re.match(r"USE\s+DATABASE\s+(\w+)\s+", query, re.IGNORECASE)
    if not database_match:
        return "Database name not found in the query."

    database_name = database_match.group(1).strip()
    remaining_query = query[database_match.end():].strip()

    # Match the query pattern for UPDATE SET
    update_set_match = re.match(
        r"UPDATE\s+(\w+)\s+SET\s+(\w+)\s+TO\s+(.+?)\s+WHERE\s+(.+)",
        remaining_query,
        re.IGNORECASE
    )

    # Match the query pattern for CHANGE TABLE NAME
    change_table_name_match = re.match(
        r"UPDATE\s+(\w+)\s+CHANGE\s+TABLE\s+NAME\s+TO\s+(\w+)",
        remaining_query,
        re.IGNORECASE
    )

    # Match the query pattern for CHANGE FIELD NAME
    change_field_name_match = re.match(
        r"UPDATE\s+(\w+)\s+CHANGE\s+FIELD\s+NAME\s+(\w+)\s+TO\s+(\w+)",
        remaining_query,
        re.IGNORECASE
    )

    if update_set_match:
        table_name = update_set_match.group(1).strip()
        change_field = update_set_match.group(2).strip()
        change_to = update_set_match.group(3).strip()
        where_clause = update_set_match.group(4).strip()

        # Convert change_to to a number if possible
        if change_to.isdigit():
            change_to = int(change_to)
        else:
            try:
                change_to = float(change_to)
            except ValueError:
                pass  # Leave it as a string if not numeric

        # Parse WHERE clause into key-value pairs
        keyvalue_pair = {}
        conditions = re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)
        for condition in conditions:
            field, value = re.match(r"(\w+)\s+WAS\s+(.+)", condition, re.IGNORECASE).groups()
            value = value.strip()

            # Convert value to a number if possible
            if value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass  # Leave it as a string if not numeric

            keyvalue_pair[field.strip()] = value

        # Call the update function with parsed components
        return update_table(database_name, table_name, keyvalue_pair, change_field, change_to)

    elif change_table_name_match:
        table_name = change_table_name_match.group(1).strip()
        change_name_to = change_table_name_match.group(2).strip()

        # Call the change table name function with parsed components
        return change_table_name(database_name, table_name, change_name_to)

    elif change_field_name_match:
        table_name = change_field_name_match.group(1).strip()
        field_name = change_field_name_match.group(2).strip()
        change_field_name_to = change_field_name_match.group(3).strip()

        # Call the change field name function with parsed components
        return change_field_name(database_name, table_name, field_name, change_field_name_to)

    else:
        return "Invalid query format."

def main():
    st.title("Database Query Executor")
    st.write("Enter a query to update the database.")

    # Input box for query
    query = st.text_area("Enter Query", placeholder="Type your query here...")

    # Execute button
    if st.button("Execute"):
        if query.strip():
            try:
                result = parse_update_query(query)
                st.text_area("Query Result", result, height=300)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please enter a query to execute.")

if __name__ == "__main__":
    main()
