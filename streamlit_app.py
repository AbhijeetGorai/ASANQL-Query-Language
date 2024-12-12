import streamlit as st
import json
import re

# Custom Query Language Functions
databases = {
    "employee_db": {
        "tables": {
            "emp_table": [
                {"name": "Alice", "id": 101},
                {"name": "Bob", "id": 102},
                {"name": "Tick", "id": 103},
                {"name": "Ricky", "id": 104}
            ],
            "dept_table": [
                {"name": "Alice", "class": "Math", "section": "A"},
                {"name": "Bob", "class": "Science", "section": "B"},
                {"name": "Sam", "class": "Biology", "section": "C"},
                {"name": "Ram", "class": "Chemistry", "section": "D"}
            ],
            "sal_table": [
                {"id": 101, "salary": 10000},
                {"id": 102, "salary": 12000},
                {"id": 103, "salary": 15000},
                {"id": 104, "salary": 20000}
            ],
            "Job": [
                {"name": "Alice",
                 "reviews": [
                     {"manager_name": "Hinu", "review": "Good"},
                     {"manager_name": "Ram", "review": "Excellent"}
                 ]
                },
                {"name": "Bob",
                 "reviews": [
                     {"manager_name": "Ramesh", "review": "Bad"},
                     {"manager_name": "Arjun", "review": "Excellent"}
                 ]
                },
                {"name": "Tick",
                 "reviews": [
                     {"manager_name": "Shyam", "review": "Good"},
                     {"manager_name": "Shinu", "review": "Excellent"}
                 ]
                },
                {"name": "Ricky",
                 "reviews": [
                     {"manager_name": "Yogesh", "review": "Good"},
                     {"manager_name": "Rishi", "review": "Excellent"}
                 ]
                }
            ],
            "store_sales":[
                {"name": "Alice",
                 "sales":[
                     {"store_name":"A", "store_revenue":200000},
                     {"store_name":"B", "store_revenue":400000},
                     {"store_name":"C", "store_revenue":500000}
                 ]
                },
                {"name": "Bob",
                 "sales":[
                     {"store_name":"A", "store_revenue":200000},
                     {"store_name":"B", "store_revenue":600000},
                     {"store_name":"C", "store_revenue":900000}
                 ]
                },
                {"name":"Tick",
                 "sales":[
                     {"store_name":"A", "store_revenue":200000},
                     {"store_name":"B", "store_revenue":300000},
                     {"store_name":"C", "store_revenue":50000}
                 ]
                },
                {"name":"Ricky",
                 "sales":[
                     {"store_name":"A", "store_revenue":200000},
                     {"store_name":"B", "store_revenue":100000},
                     {"store_name":"C", "store_revenue":30000}
                 ]
                }

            ]
        }
    }
}

def update_field_value(databases, database_name, table_name, keyvalue_pair, change_field, change_to):
    db_data = databases.get(database_name, {}).get("tables", {})
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
        st.write(databases[database_name]["tables"][table_name])
    else:
        st.warning("No rows matched the condition, table not updated.")

def update_table_name(databases, database_name, table_name, change_to_name):
    if database_name in databases:
        db = databases[database_name]
        if "tables" in db and table_name in db["tables"]:
            db["tables"][change_to_name] = db["tables"].pop(table_name)
            st.success(f"Table name changed from '{table_name}' to '{change_to_name}' in database '{database_name}'.")
        else:
            st.error(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        st.error(f"Database '{database_name}' not found.")

def update_field_name(databases, database_name, table_name, field_name, change_to_name):
    if database_name in databases:
        db = databases[database_name]
        if "tables" in db and table_name in db["tables"]:
            table = db["tables"][table_name]
            for row in table:
                if field_name in row:
                    row[change_to_name] = row.pop(field_name)
            st.success(f"Field name changed from '{field_name}' to '{change_to_name}' in table '{table_name}' within database '{database_name}'.")
        else:
            st.error(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        st.error(f"Database '{database_name}' not found.")

def update_table(database_name, table_name, keyvalue_pair, change_field, change_to):
    update_field_value(databases, database_name, table_name, keyvalue_pair, change_field, change_to)

def change_table_name(database_name, table_name, change_name_to):
    update_table_name(databases, database_name, table_name, change_name_to)

def change_field_name(database_name, table_name, field_name, change_field_name_to):
    update_field_name(databases, database_name, table_name, field_name, change_field_name_to)

def parse_update_query(databases, query):
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

    else:
        st.error("Invalid query format.")

# Set the title of the app
st.title("JSON Database Management")

# Input box for entering queries
query = st.text_area("Enter your query:", height=100)

# Button to execute the query
if st.button("Execute Query"):
    if query:
        parse_update_query(databases, query)
    else:
        st.warning("Please enter a query.")

# Display the current database
st.header("Current Database")
st.write(databases)
