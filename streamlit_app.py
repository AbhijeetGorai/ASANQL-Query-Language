import streamlit as st
import json
import re

# Function to load JSON data from a file
def load_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to save JSON data to a file
def save_json_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# File path to the JSON data
file_path = 'data1.json'

# Load the JSON data
databases = load_json_data(file_path)

def update_field_value(database_name, table_name, keyvalue_pair, change_field, change_to):
    db_data = databases.get("databases", {}).get(database_name, {})
    table_data = db_data.get(table_name, None)
    if not table_data:
        st.error(f"Table {table_name} not found in database {database_name}.")
        return False

    updated = False
    for row in table_data:
        if all(row.get(k) == v for k, v in keyvalue_pair.items()):
            if change_field in row:
                row[change_field] = change_to
                updated = True
            else:
                st.error(f"Field '{change_field}' not found in row: {row}")

    if updated:
        st.success("Table updated successfully.")
        st.write(databases["databases"][database_name][table_name])
        # Save the modified data back to the file
        save_json_data(file_path, databases)
    else:
        st.warning("No rows matched the condition, table not updated.")

def update_table_name(database_name, table_name, change_to_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            # Rename the table
            db[change_to_name] = db.pop(table_name)
            st.success(f"Table name changed from '{table_name}' to '{change_to_name}' in database '{database_name}'.")
            # Save the modified data back to the file
            save_json_data(file_path, databases)
        else:
            st.error(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        st.error(f"Database '{database_name}' not found.")

def update_field_name(database_name, table_name, field_name, change_to_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            table = db[table_name]
            for row in table:
                if field_name in row:
                    # Rename the field in each row
                    row[change_to_name] = row.pop(field_name)
            st.success(f"Field name changed from '{field_name}' to '{change_to_name}' in table '{table_name}' within database '{database_name}'.")
            # Save the modified data back to the file
            save_json_data(file_path, databases)
        else:
            st.error(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        st.error(f"Database '{database_name}' not found.")

def show_table_content(database_name, table_name):
    db_data = databases.get("databases", {}).get(database_name, {})
    table_data = db_data.get(table_name, None)
    if not table_data:
        st.error(f"Table {table_name} not found in database {database_name}.")
        return

    st.write(f"Content of table '{table_name}' in database '{database_name}':")
    st.json(table_data)

def show_databases():
    db_names = list(databases.get("databases", {}).keys())
    st.write("Databases:")
    st.json(db_names)

def update_table(database_name, table_name, keyvalue_pair, change_field, change_to):
    update_field_value(database_name, table_name, keyvalue_pair, change_field, change_to)

def change_table_name(database_name, table_name, change_name_to):
    update_table_name(database_name, table_name, change_name_to)

def change_field_name(database_name, table_name, field_name, change_field_name_to):
    update_field_name(database_name, table_name, field_name, change_field_name_to)

def parse_update_query(query):
    database_match = re.match(r"USE\s+(\w+)\s+", query, re.IGNORECASE)
    if not database_match:
        st.error("Database name not found in the query.")
        return

    database_name = database_match.group(1).strip()
    remaining_query = query[database_match.end():].strip()

    update_set_match = re.match(
        r"UPDATE\s+(\w+)\s+SET\s+(\w+)\s+TO\s+(.+?)\s+WHERE\s+(.+)",
        remaining_query,
        re.IGNORECASE
    )

    change_table_name_match = re.match(
        r"UPDATE\s+(\w+)\s+CHANGE\s+TABLE\s+NAME\s+TO\s+(\w+)",
        remaining_query,
        re.IGNORECASE
    )

    change_field_name_match = re.match(
        r"UPDATE\s+(\w+)\s+CHANGE\s+FIELD\s+NAME\s+(\w+)\s+TO\s+(\w+)",
        remaining_query,
        re.IGNORECASE
    )

    show_table_match = re.match(
        r"SHOW\s+TABLE\s+(\w+)",
        remaining_query,
        re.IGNORECASE
    )

    if update_set_match:
        table_name = update_set_match.group(1).strip()
        change_field = update_set_match.group(2).strip()
        change_to = update_set_match.group(3).strip()
        where_clause = update_set_match.group(4).strip()

        if change_to.isdigit():
            change_to = int(change_to)
        else:
            try:
                change_to = float(change_to)
            except ValueError:
                pass

        keyvalue_pair = {}
        conditions = re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)
        for condition in conditions:
            field, value = re.match(r"(\w+)\s+WAS\s+(.+)", condition, re.IGNORECASE).groups()
            value = value.strip()

            if value.isdigit():
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass

            keyvalue_pair[field.strip()] = value

        update_table(database_name, table_name, keyvalue_pair, change_field, change_to)

    elif change_table_name_match:
        table_name = change_table_name_match.group(1).strip()
        change_name_to = change_table_name_match.group(2).strip()
        change_table_name(database_name, table_name, change_name_to)

    elif change_field_name_match:
        table_name = change_field_name_match.group(1).strip()
        field_name = change_field_name_match.group(2).strip()
        change_field_name_to = change_field_name_match.group(3).strip()
        change_field_name(database_name, table_name, field_name, change_field_name_to)

    elif show_table_match:
        table_name = show_table_match.group(1).strip()
        show_table_content(database_name, table_name)

    else:
        st.error("Invalid query format.")

def parse_show_databases_query(query):
    show_databases_match = re.match(r"SHOW\s+DATABASES;", query, re.IGNORECASE)
    if show_databases_match:
        show_databases()
    else:
        st.error("Invalid query format.")

# Set the title of the app
st.title("JSON Database Management")

# Input box for entering queries
query = st.text_area("Enter your query:", height=100)

# Button to execute the query
if st.button("Execute Query"):
    if query:
        if query.strip().upper().startswith("SHOW DATABASES;"):
            parse_show_databases_query(query)
        else:
            parse_update_query(query)
    else:
        st.warning("Please enter a query.")

# Display the current database
st.header("Current Database")
st.write(databases)
