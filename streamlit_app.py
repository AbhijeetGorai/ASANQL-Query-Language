import re
import json
import streamlit as st
# Function to load the database from a JSON file
def load_database(file_path):
    global databases
    with open(file_path, 'r') as file:
        databases = json.load(file)

# Function to save the database to a JSON file
def save_database(file_path):
    with open(file_path, 'w') as file:
        json.dump(databases, file, indent=4)

# Helper function to evaluate conditions
def evaluate_condition(row, condition):
    # Handle 'IS' and 'NOT IS'
    if "IS" in condition and "NOT IS" not in condition:
        field, value = condition.split("IS")
        field, value = field.strip(), value.strip().strip("'")
        field_value = row.get(field)
        if isinstance(field_value, list):
          # If the value is present inside a list
          return value in field_value
        else:
            return str(field_value) == value
    elif "NOT IS" in condition:
        field, value = condition.split("NOT IS")
        field, value = field.strip(), value.strip().strip("'")
        field_value = row.get(field)
        if isinstance(field_value, list):
          # If the value is present inside a list
          return value not in field_value
        else:
            return str(field_value) != value
    # Handle 'HAS' and 'NOT HAS'
    elif "HAS" in condition and "NOT HAS" not in condition:
        field, values = condition.split("HAS")
        field = field.strip()
        values = eval(values.strip())  # Convert the string representation of the list into an actual list
        field_value = row.get(field)
        if isinstance(field_value, list):
          # If the value is present inside a list
          return all(v in field_value for v in values)
        else:
            return any(str(field_value) == v for v in values)
    elif "NOT HAS" in condition:
        field, values = condition.split("NOT HAS")
        field = field.strip()
        values = eval(values.strip())  # Convert the string representation of the list into an actual list
        field_value = row.get(field)
        if isinstance(field_value, list):
          return all(v in field_value for v in values)
        else:
            return all(str(field_value) != v for v in values)
    return False

def where_filter(where_clause, joined_data):
  filtered_list1 = []
  count = 0
  and_cond = []
  and_count = 0
  and_list, or_list = separate_conditions(where_clause)
  if len(and_list) == 0 or len(or_list) == 0:
    for row in joined_data:
      res = evaluate_condition(row, where_clause)
      if res == True:
        filtered_list1.append(row)
  else:
    and_count = len(and_list)
    for row in joined_data:
      for i in and_list:
        result = evaluate_condition(row, i)
        if result == True:
          count = count + 1
          and_cond.append(row)
      for i in or_list:
        result = evaluate_condition(row, i)
        if result == True:
          filtered_list1.append(row)
  if count != and_count:
    print("Not passed")
  else:
    for i in and_cond:
      filtered_list1.append(i)
  filtered_list1 = [dict(t) for t in {tuple(d.items()) for d in filtered_list1}]
  return filtered_list1

def separate_conditions(where_clause):
    and_conditions = []
    or_conditions = []
    results = []

    # Clean the where_clause by replacing AND/OR with spaces
    where_clause_cleaned = where_clause.replace("AND", " ").replace("OR", " ")
    parts = [' '.join(item.split()) for item in where_clause_cleaned.split('  ') if item.strip()]

    for i, condition in enumerate(parts):
        # Find the position of the condition in where_clause
        start_idx = where_clause.find(condition)

        # Get the prefix (word before the condition)
        prefix = where_clause[:start_idx].strip().split()[-1] if start_idx > 0 else None

        # Get the suffix (word after the condition)
        end_idx = start_idx + len(condition)
        suffix = where_clause[end_idx:].strip().split()[0] if end_idx < len(where_clause) else None

        # Classification logic
        if i == 0:  # First condition
            if suffix == "AND":
                and_conditions.append(condition)
            elif suffix == "OR":
                or_conditions.append(condition)
        else:  # Other conditions
            if prefix == "AND":
                and_conditions.append(condition)
            elif prefix == "OR":
                or_conditions.append(condition)

    # Combine the results for easier readability or additional processing
    return and_conditions, or_conditions

def perform_aggregation(joined_data, aggregation_operation, fields):
    """
    Perform aggregation on the provided data directly based on the aggregation operation.
    Parameters:
    - joined_data (list of dict): List of dictionaries representing the data.
    - aggregation_operation (str): Aggregation operation (e.g., "ITS COMBINED field_name").
    - fields (list): List of fields to be selected.
    Returns:
    - list of dict: The updated data with aggregation results.
    """
    aggregates = ["ITS COMBINED", "COUNT THE", "MAXIMUM", "MINIMUM", "AVERAGE"]

    # Identify the operation and field
    for agg_command in aggregates:
        if agg_command in aggregation_operation:
            field = aggregation_operation.split(agg_command)[1].strip()
            if len(fields) == 1:
                # Perform aggregation across all rows
                field_values = []
                for row in joined_data:
                    if isinstance(row.get(field), list):  # If the value is a list
                        field_values.extend(row[field])
                    elif isinstance(row.get(field), (int, float, str)):  # If the value is a number
                        field_values.append(row[field])
                if agg_command == "ITS COMBINED":
                    agg_result = sum(field_values)
                elif agg_command == "COUNT THE":
                    agg_result = len(field_values)
                elif agg_command == "MAXIMUM":
                    agg_result = max(field_values)
                elif agg_command == "MINIMUM":
                    agg_result = min(field_values)
                elif agg_command == "AVERAGE":
                    agg_result = sum(field_values) / len(field_values) if field_values else 0
                return [{f"{agg_command} {field}": agg_result}]
            else:
                # Perform aggregation within each group
                group_field = fields[0]  # Assuming the first field is the grouping field
                grouped_data = {}

                # Group the data by the specified field
                for row in joined_data:
                    group_key = row.get(group_field)
                    if group_key not in grouped_data:
                        grouped_data[group_key] = []
                    grouped_data[group_key].append(row[field])

                # Perform the aggregation within each group
                aggregated_results = []
                for group_key, field_values in grouped_data.items():
                    if agg_command == "ITS COMBINED":
                        agg_result = sum(field_values)
                    elif agg_command == "COUNT THE":
                        agg_result = len(field_values)
                    elif agg_command == "MAXIMUM":
                        agg_result = max(field_values)
                    elif agg_command == "MINIMUM":
                        agg_result = min(field_values)
                    elif agg_command == "AVERAGE":
                        agg_result = sum(field_values) / len(field_values) if field_values else 0
                    aggregated_results.append({group_field: group_key, f"{agg_command} {field}": agg_result})

                return aggregated_results
    return joined_data

def check_and_flatten_json_table(table_data):
    """
    Checks if the table contains any JSON lists (e.g., 'reviews'). If a JSON list is found,
    flattens the table structure and returns the flattened table.

    Args:
        table_data (list): List of rows in the table.
    Returns:
        list: Flattened table if a JSON list is found, or the original table otherwise.
    """
    contains_json_list = False

    # Iterate through each row in the table to check for JSON lists
    for row in table_data:
        for key, value in row.items():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                contains_json_list = True
                break  # Exit loop if a JSON list is found
        if contains_json_list:
            break
    # If a JSON list is found, flatten the table
    if contains_json_list:
        return True

    # If no JSON list is found, return the original table
    return False

# Function to parse and execute the query
def parse_query(query):
    # Step 1: Validate "USE DATABASE"
    if "USE DATABASE" not in query:
        return "Invalid query format. Please specify the database using 'USE DATABASE <database_name>'."
    try:
        use_db_index = query.index("USE DATABASE") + len("USE DATABASE")
    except ValueError:
        return "Invalid query format. Please specify the database using 'USE DATABASE <database_name>'."
    db_end_index = query.find("FIND")
    if db_end_index == -1:
        return "Invalid query format. 'FIND' statement is missing after database specification."
    # Extract database name
    database_name = query[use_db_index:db_end_index].strip()
    if database_name not in databases["databases"]:
        return f"Database '{database_name}' not found."
    # Step 2: Extract "FIND" fields
    find_index = query.index("FIND") + len("FIND")
    from_table_index = query.index("FROM THE TABLE")
    find_part = query[find_index:from_table_index].strip()
    fields = []
    select_all = False
    if find_part == "*":
        select_all = True
    else:
        fields = [field.strip() for field in find_part.split("AND")]
    # Extract table names and validate WHERE clause
    table_names_part = query[from_table_index + len("FROM THE TABLE"):].strip()

    where_clause = None
    join_fields = []
    join_types = []
    with_clause = 0
    if "WHERE" in table_names_part:
        table_names_part, where_clause = table_names_part.split("WHERE", 1)
        where_clause = where_clause.strip()

    if "WITH" in table_names_part:
        with_clause = 1
        table_names_part, join_field_part = table_names_part.split("WITH", 1)
        join_field_part = join_field_part.strip()
        join_fields = []
        for join_spec in join_field_part.split("AND"):
            join_spec = join_spec.strip()
            if join_spec.startswith("LEFT"):
                join_types.append("LEFT")
                join_fields.append(join_spec.replace("LEFT", "").strip())
            elif join_spec.startswith("RIGHT"):
                join_types.append("RIGHT")
                join_fields.append(join_spec.replace("RIGHT", "").strip())
            elif join_spec.startswith("FULL"):
                join_types.append("FULL")
                join_fields.append(join_spec.replace("FULL", "").strip())
            else:
                join_types.append("INNER")
                join_fields.append(join_spec.strip())
    table_names = table_names_part.split("AND")
    table_names = [table.strip() for table in table_names]

    # Condition for checking if the WITH clause is present if more than 1 table is present
    if len(table_names) > 1 and with_clause == 0:
      print("Include WITH clause for joining 2 tables")
    # Validate tables
    table_metadata = databases["databases"][database_name]
    for table_name in table_names:
        if table_name not in table_metadata:
            return f"Table '{table_name}' not found in database '{database_name}'."

    for table_name in table_names:
      table_data = databases["databases"][database_name].get(table_name)
      json_check = check_and_flatten_json_table(table_data)
      if json_check:
        table_results = flatten_and_filter_nested_json(table_data)
        table_metadata[table_name] = table_results
      else:
        continue
    # Fetch the table data
    joined_data = table_metadata[table_names[0]]

    # Step 3: Perform table joins
    for i in range(1, len(table_names)):
        next_table = table_metadata[table_names[i]]
        join_type = join_types[i - 1] if i - 1 < len(join_types) else "INNER"
        join_field = join_fields[i - 1] if i - 1 < len(join_fields) else None
        if not join_field:
            return "Join field must be specified for all joins."
        temp_data = []
        if join_type == "FULL":
            matched_right_rows = set()
            # Perform the LEFT JOIN part
            for row1 in joined_data:
                matched = False
                for row2 in next_table:
                    left_key = row1.get(join_field) or row1.get(f"{join_field}_left") or row1.get(f"{join_field}_right")
                    right_key = row2.get(join_field)
                    if left_key == right_key:  # Match found
                        merged_row = {
                            **{f"{key}_left": row1.get(key) for key in row1},
                            **{f"{key}_right": row2.get(key) for key in row2}
                        }
                        temp_data.append(merged_row)
                        matched = True
                        matched_right_rows.add(tuple(row2.items()))
                # Handle unmatched LEFT JOIN rows
                if not matched:
                    null_row = {f"{key}_right": None for key in next_table[0].keys()}
                    temp_data.append({**{f"{key}_left": row1.get(key) for key in row1}, **null_row})
            # Add unmatched RIGHT JOIN rows
            for row2 in next_table:
                if tuple(row2.items()) not in matched_right_rows:
                    null_row = {f"{key}_left": None for key in joined_data[0].keys()}
                    temp_data.append({**null_row, **{f"{key}_right": row2.get(key) for key in row2}})
        elif join_type == "RIGHT":
            for row2 in next_table:
                matched = False
                for row1 in joined_data:
                    left_key = row1.get(join_field) or row1.get(f"{join_field}_left") or row1.get(f"{join_field}_right")
                    right_key = row2.get(join_field)
                    if left_key == right_key:
                        merged_row = {
                            **{f"{key}_left": row1.get(key) for key in row1},
                            **{f"{key}_right": row2.get(key) for key in row2}
                        }
                        temp_data.append(merged_row)
                        matched = True
                if not matched:
                    null_row = {f"{key}_left": None for key in joined_data[0].keys()}
                    temp_data.append({**null_row, **{f"{key}_right": row2.get(key) for key in row2}})
        elif join_type == "LEFT":
            for row1 in joined_data:
                matched = False
                for row2 in next_table:
                    left_key = row1.get(join_field) or row1.get(f"{join_field}_left") or row1.get(f"{join_field}_right")
                    right_key = row2.get(join_field)
                    if left_key == right_key:
                        merged_row = {
                            **{f"{key}_left": row1.get(key) for key in row1},
                            **{f"{key}_right": row2.get(key) for key in row2}
                        }
                        temp_data.append(merged_row)
                        matched = True
                if not matched:
                    null_row = {f"{key}_right": None for key in next_table[0].keys()}
                    temp_data.append({**{f"{key}_left": row1.get(key) for key in row1}, **null_row})
        elif join_type == "INNER":
            for row1 in joined_data:
                for row2 in next_table:
                    left_key = row1.get(join_field) or row1.get(f"{join_field}_left") or row1.get(f"{join_field}_right")
                    right_key = row2.get(join_field)
                    if left_key == right_key:
                        merged_row = {
                            **{f"{key}_left": row1.get(key) for key in row1},
                            **{f"{key}_right": row2.get(key) for key in row2}
                        }
                        temp_data.append(merged_row)
        joined_data = temp_data

    filtered_result = []
    if where_clause:
      res1 = where_filter(where_clause, joined_data)
      filtered_result = res1
    else:
      filtered_result = joined_data

    joined_data = filtered_result
    # Step 4: Perform Aggregations
    # Define Aggregates
    aggregates = ["ITS COMBINED", "COUNT THE", "MAXIMUM", "MINIMUM", "AVERAGE"]
    for i in fields:
      for j in aggregates:
        if j in i:
          joined_data = perform_aggregation(joined_data, i, fields)

    # Step 5: Filter results based on FIND fields
    if not select_all:
        filtered_data = []
        for row in joined_data:
            filtered_row = {field: row.get(field, None) for field in fields}
            filtered_data.append(filtered_row)
        joined_data = filtered_data

    joined_data = [dict(t) for t in {tuple(d.items()) for d in joined_data}]
    print(joined_data)

# Update function begins from here

def update_field_value(database_name, table_name, keyvalue_pair, change_field, change_to):
    # Locate the table in the specified database
    db_data = databases.get("databases", {}).get(database_name, {})
    table_data = db_data.get(table_name, None)
    if not table_data:
        print(f"Table {table_name} not found in database {database_name}.")
        return False

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
                print(f"Field '{change_field}' not found in row: {row}")

    if updated:
      print("Table updated successfully.")
      print(databases["databases"][database_name][table_name])
    else:
      print("No rows matched the condition, table not updated.")

def update_table_name(database_name, table_name, change_to_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            # Rename the table
            db[change_to_name] = db.pop(table_name)
            print(f"Table name changed from '{table_name}' to '{change_to_name}' in database '{database_name}'.")
        else:
            print(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        print(f"Database '{database_name}' not found.")

def update_field_name(database_name, table_name, field_name, change_to_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            table = db[table_name]
            for row in table:
                if field_name in row:
                    # Rename the field in each row
                    row[change_to_name] = row.pop(field_name)
            print(f"Field name changed from '{field_name}' to '{change_to_name}' in table '{table_name}' within database '{database_name}'.")
        else:
            print(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        print(f"Database '{database_name}' not found.")

def update_table(database_name, table_name, keyvalue_pair, change_field, change_to):
    # This is a placeholder for the actual update logic
    # You should implement the logic to update the table in the database

    update_field_value(database_name, table_name, keyvalue_pair, change_field, change_to)

def change_table_name(database_name, table_name, change_name_to):
    # This is a placeholder for the actual logic to change the table name

    update_table_name(database_name, table_name, change_name_to)

def change_field_name(database_name, table_name, field_name, change_field_name_to):
    # This is a placeholder for the actual logic to change the field name

    update_field_name(database_name, table_name, field_name, change_field_name_to)

def parse_update_query(query):
    # Extract the database name
    database_match = re.match(r"USE\s+DATABASE\s+(\w+)\s+", query, re.IGNORECASE)
    if not database_match:
        raise ValueError("Database name not found in the query.")

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
        result = update_table(database_name, table_name, keyvalue_pair, change_field, change_to)
        return result

    elif change_table_name_match:
        table_name = change_table_name_match.group(1).strip()
        change_name_to = change_table_name_match.group(2).strip()

        # Call the change table name function with parsed components
        result = change_table_name(database_name, table_name, change_name_to)
        return result

    elif change_field_name_match:
        table_name = change_field_name_match.group(1).strip()
        field_name = change_field_name_match.group(2).strip()
        change_field_name_to = change_field_name_match.group(3).strip()

        # Call the change field name function with parsed components
        result = change_field_name(database_name, table_name, field_name, change_field_name_to)
        return result

    else:
        raise ValueError("Invalid query format.")

# Alter function begins from here

def alter_parse_query(query):
    # Extract database name
    db_name_match = re.search(r'USE DATABASE (\w+)', query)
    db_name = db_name_match.group(1) if db_name_match else None

    # Extract table name
    table_name_match = re.search(r'ALTER (\w+)', query)
    table_name = table_name_match.group(1) if table_name_match else None

    # Extract where clause
    where_clause_match = re.search(r'WHERE (\w+) IS (\w+)', query)
    where_clause = {where_clause_match.group(1): where_clause_match.group(2)} if where_clause_match else None

    # Determine the type of query
    if "ADD ROW" in query:
        # Extract list name
        list_name_match = re.search(r'TO LIST (\w+)', query)
        list_name = list_name_match.group(1) if list_name_match else None

        # Extract row data
        row_data_match = re.search(r'ADD ROW (\[.*?\])', query)
        row_data_str = row_data_match.group(1) if row_data_match else None
        row_data = json.loads(row_data_str.replace("'", "\"")) if row_data_str else None

        return "add_row", db_name, table_name, list_name, row_data, where_clause

    elif "CREATE FIELD" in query and "WITH VALUE" in query:
        # Extract new field name
        field_name_match = re.search(r'CREATE FIELD (\w+)', query)
        new_field_name = field_name_match.group(1) if field_name_match else None

        # Extract new value
        value_match = re.search(r'WITH VALUE (\d+)', query)
        new_value = int(value_match.group(1)) if value_match else None

        return "add_field", db_name, table_name, new_field_name, new_value, where_clause

    elif "CREATE FIELD" in query and "WITH LIST NAME" in query:
        # Extract list name
        list_name_match = re.search(r'WITH LIST NAME (\w+)', query)
        list_name = list_name_match.group(1) if list_name_match else None

        # Extract values
        values_match = re.search(r'CREATE FIELD (\[.*?\])', query)
        values_str = values_match.group(1) if values_match else None
        values = json.loads(values_str.replace("'", "\"")) if values_str else None

        return "add_nested_field", db_name, table_name, list_name, values, where_clause

    else:
        return None, None, None, None, None, None

def add_row_to_json_list(db_name, table_name, list_name, row_data, name_filter=None):
    if db_name in databases["databases"]:
        db = databases["databases"][db_name]
        if table_name in db:
            table = db[table_name]
            for entry in table:
                if name_filter and entry.get("name") != name_filter:
                    continue  # Skip entries that do not match the name_filter
                if list_name not in entry:
                    entry[list_name] = []
                if isinstance(entry[list_name], list):
                    if isinstance(row_data, list) and all(isinstance(row, dict) for row in row_data):
                        entry[list_name].extend(row_data)
                        if name_filter:
                            break  # If name_filter is provided, stop after processing the matching entry
                    else:
                        print("Invalid row data. It should be a list of dictionaries.")
                        return
            else:
                if name_filter:
                    print(f"No entry with name '{name_filter}' found in table '{table_name}'.")
                else:
                    print(f"List '{list_name}' added to all entries in table '{table_name}'.")
        else:
            print(f"Table '{table_name}' not found in database '{db_name}'.")
    else:
        print(f"Database '{db_name}' not found.")

def add_field_to_table(db_name, table_name, new_field_name, new_value, where_clause):
    if db_name and table_name and new_field_name and new_value is not None:
        # Find the table in the database
        table = databases["databases"].get(db_name, {}).get(table_name, [])

        # Update the table with the new field and value based on the where clause
        if where_clause:
            for record in table:
                if all(record.get(key) == value for key, value in where_clause.items()):
                    record[new_field_name] = new_value
        else:
            for record in table:
                record[new_field_name] = new_value
    else:
        print("Invalid query or parameters.")

def add_nested_field_to_table(db_name, table_name, list_name, values, where_clause):
    if db_name and table_name and list_name and values is not None:
        # Find the table in the database
        table = databases["databases"].get(db_name, {}).get(table_name, [])

        # Update the table with the new nested field based on the where clause
        if where_clause:
            for record in table:
                if all(record.get(key) == value for key, value in where_clause.items()):
                    record[list_name] = values
        else:
            for record in table:
                record[list_name] = values
    else:
        print("Invalid query or parameters.")

def alter_execute_query(query):
    query_type, db_name, table_name, param3, param4, where_clause = alter_parse_query(query)

    if query_type == "add_row":
        add_row_to_json_list(db_name, table_name, param3, param4, where_clause.get("name") if where_clause else None)
    elif query_type == "add_field":
        add_field_to_table(db_name, table_name, param3, param4, where_clause)
    elif query_type == "add_nested_field":
        add_nested_field_to_table(db_name, table_name, param3, param4, where_clause)
    else:
        print("Invalid query type.")

    # Print the updated table structure
    if db_name in databases["databases"] and table_name in databases["databases"][db_name]:
        table = databases["databases"][db_name][table_name]
        print(f"\nUpdated {table_name} table in {db_name} database:")
        for record in table:
            print(record)

# Delete function begins from here

def delete_parse_query(query):
    # Extract database name
    db_name_match = re.search(r'USE DATABASE (\w+)', query)
    db_name = db_name_match.group(1) if db_name_match else None

    # Extract table name
    table_name_match = re.search(r'DELETE TABLE (\w+)', query)
    table_name = table_name_match.group(1) if table_name_match else None

    # Extract field name
    field_name_match = re.search(r'DELETE FIELD (\w+)', query)
    field_name = field_name_match.group(1) if field_name_match else None

    # Extract list name
    list_name_match = re.search(r'WITHIN LIST (\w+)', query)
    list_name = list_name_match.group(1) if list_name_match else None

    # Extract list field name
    list_field_name_match = re.search(r'DELETE LIST FIELD (\w+)', query)
    list_field_name = list_field_name_match.group(1) if list_field_name_match else None

    # Extract table name from the end of the query
    table_name_end_match = re.search(r'IN TABLE (\w+)', query)
    table_name_end = table_name_end_match.group(1) if table_name_end_match else None

    # Determine the type of query
    if "DELETE DATABASE" in query:
        if db_name_match:
            return "delete_database", db_name
        else:
            db_name_match = re.search(r'DELETE DATABASE (\w+)', query)
            db_name = db_name_match.group(1) if db_name_match else None
            return "delete_database", db_name
    elif "DELETE TABLE" in query:
        return "delete_table", db_name, table_name
    elif "DELETE FIELD" in query and "WITHIN LIST" in query:
        return "delete_field_within_list", db_name, table_name_end, field_name, list_name
    elif "DELETE FIELD" in query:
        return "delete_field", db_name, table_name_end, field_name
    elif "DELETE LIST FIELD" in query:
        return "delete_list_field", db_name, table_name_end, list_field_name
    else:
        return None, None, None, None, None

def delete_database(db_name):
    if db_name in databases["databases"]:
        del databases["databases"][db_name]
        print(f"Database '{db_name}' deleted successfully.")
    else:
        print(f"Database '{db_name}' not found.")

def delete_table(db_name, table_name):
    if db_name in databases["databases"]:
        db = databases["databases"][db_name]
        if table_name in db:
            del db[table_name]
            print(f"Table '{table_name}' deleted successfully from database '{db_name}'.")
        else:
            print(f"Table '{table_name}' not found in database '{db_name}'.")
    else:
        print(f"Database '{db_name}' not found.")

def delete_field(db_name, table_name, field_name):
    if db_name in databases["databases"]:
        db = databases["databases"][db_name]
        if table_name in db:
            table = db[table_name]
            for record in table:
                if field_name in record:
                    del record[field_name]
            print(f"Field '{field_name}' deleted successfully from table '{table_name}' in database '{db_name}'.")
            return table
        else:
            print(f"Table '{table_name}' not found in database '{db_name}'.")
    else:
        print(f"Database '{db_name}' not found.")

def delete_field_within_list(db_name, table_name, field_name, list_name):
    if db_name in databases["databases"]:
        db = databases["databases"][db_name]
        if table_name in db:
            table = db[table_name]
            for record in table:
                if list_name in record:
                    for item in record[list_name]:
                        if field_name in item:
                            del item[field_name]
            print(f"Field '{field_name}' within list '{list_name}' deleted successfully from table '{table_name}' in database '{db_name}'.")
            return table
        else:
            print(f"Table '{table_name}' not found in database '{db_name}'.")
    else:
        print(f"Database '{db_name}' not found.")

def delete_list_field(db_name, table_name, list_field_name):
    if db_name in databases["databases"]:
        db = databases["databases"][db_name]
        if table_name in db:
            table = db[table_name]
            for record in table:
                if list_field_name in record:
                    del record[list_field_name]
            print(f"List field '{list_field_name}' deleted successfully from table '{table_name}' in database '{db_name}'.")
            return table
        else:
            print(f"Table '{table_name}' not found in database '{db_name}'.")
    else:
        print(f"Database '{db_name}' not found.")

def execute_delete_query(query):
    query_type, *params = delete_parse_query(query)

    if query_type == "delete_database":
        delete_database(*params)
    elif query_type == "delete_table":
        delete_table(*params)
    elif query_type == "delete_field":
        table = delete_field(*params)
        if table:
            print(f"\nUpdated {params[1]} table in {params[0]} database:")
            print(json.dumps(table, indent=4))
    elif query_type == "delete_field_within_list":
        table = delete_field_within_list(*params)
        if table:
            print(f"\nUpdated {params[1]} table in {params[0]} database:")
            print(json.dumps(table, indent=4))
    elif query_type == "delete_list_field":
        table = delete_list_field(*params)
        if table:
            print(f"\nUpdated {params[1]} table in {params[0]} database:")
            print(json.dumps(table, indent=4))
    else:
        print("Invalid query type.")

# Alter function begins from here

def create_table_in_database(database_name, table_name, value_row):
    # Check if the database exists
    if database_name not in databases["databases"]:
        print(f"Database '{database_name}' not found.")
        return

    # Check if the table already exists
    if table_name in databases["databases"][database_name]:
        print(f"Table '{table_name}' already exists in database '{database_name}'.")
        return

    # Create the new table with the given value row
    databases["databases"][database_name][table_name] = [value_row]
    print(f"Table '{table_name}' created in database '{database_name}' with values: {value_row}")

def parse_create_table_query(query):
    # Extract the database name
    database_match = re.match(r"USE DATABASE (\w+)\s+", query, re.IGNORECASE)
    if not database_match:
        raise ValueError("Database name not found in the query.")

    database_name = database_match.group(1).strip()
    remaining_query = query[database_match.end():].strip()

    # Extract the table name and values
    create_table_match = re.match(
        r"CREATE TABLE (\w+) WITH VALUES (\{.*\})",
        remaining_query,
        re.IGNORECASE
    )

    if create_table_match:
        table_name = create_table_match.group(1).strip()
        value_row_str = create_table_match.group(2).strip()

        # Convert the value row string to a dictionary
        value_row = json.loads(value_row_str.replace("'", "\""))

        # Call the create table function with parsed components
        create_table_in_database(database_name, table_name, value_row)
    else:
        raise ValueError("Invalid query format.")

def create_database(database_name):
    # Check if the database already exists
    if database_name in databases["databases"]:
        print(f"Database '{database_name}' already exists.")
        return

    # Create the new database
    databases["databases"][database_name] = {}
    print(f"Database '{database_name}' created.")

def parse_create_database_query(query):
    # Extract the database name
    create_db_match = re.match(r"CREATE DATABASE (\w+)", query, re.IGNORECASE)
    if not create_db_match:
        raise ValueError("Database name not found in the query.")

    database_name = create_db_match.group(1).strip()

    # Call the create database function with the parsed database name
    create_database(database_name)

# Function to show the content of a table
def show_table_content(database_name, table_name):
    if database_name in databases["databases"]:
        db = databases["databases"][database_name]
        if table_name in db:
            table = db[table_name]
            print(f"Content of table '{table_name}' in database '{database_name}':")
            for record in table:
                print(record)
        else:
            print(f"Table '{table_name}' not found in database '{database_name}'.")
    else:
        print(f"Database '{database_name}' not found.")

# Function to list all database names
def list_all_databases():
    print("Databases:")
    for db_name in databases["databases"].keys():
        print(db_name)

# Function to call the relevant parsing function based on the query
# Function to call the relevant parsing function based on the query
def execute_query(query):
    if query.startswith("USE DATABASE"):
        if "FIND" in query:
            parse_query(query)
        elif "UPDATE" in query:
            parse_update_query(query)
        elif "DELETE" in query:
            execute_delete_query(query)
        elif "ALTER" in query:
            alter_execute_query(query)
        elif "CREATE" in query:
            parse_create_table_query(query)
        elif "SHOW TABLE" in query:
            # Extract database name and table name
            db_name_match = re.search(r'USE DATABASE (\w+)', query)
            table_name_match = re.search(r'SHOW TABLE (\w+)', query)
            if db_name_match and table_name_match:
                database_name = db_name_match.group(1)
                table_name = table_name_match.group(1)
                show_table_content(database_name, table_name)
            else:
                print("Invalid query format for showing table content.")
        else:
            print("Invalid query format.")
    elif query.startswith("CREATE DATABASE"):
        parse_create_database_query(query)
    elif query.startswith("DELETE DATABASE"):
        execute_delete_query(query)
    elif query.startswith("SHOW DATABASES"):
        list_all_databases()
    else:
        print("Invalid query format.")

# Step 1: Load the database
database_file = 'data1.json'
# Streamlit app
def main():
    st.title("Database Query Executor") 
    database = load_database(database_file)

    # Step 2: Query Execution
    query = st.text_input("Enter your query (e.g., SHOW DATABASES):")

    if st.button("Execute"):
        # Execute the query
        result = execute_query(database, query)

        # Step 3: Save the updated database
        save_database(database_file)

        # Display query result
        st.subheader("Query Result:")
        st.json(result)

        # Display updated database structure
        st.subheader("Updated Database Structure:")
        st.json(database)

if __name__ == "__main__":
    main()

