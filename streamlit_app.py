import streamlit as st
import custom_query  # Import your custom query language module

# Set the title of the app
st.title("JSON Database Management")

# Sidebar with input fields
st.sidebar.header("User Input")

# Add Record Component
st.sidebar.subheader("Add Record")
new_id = st.sidebar.number_input("Enter ID:", min_value=1)
new_name = st.sidebar.text_input("Enter Name:")
new_age = st.sidebar.number_input("Enter Age:", min_value=0, max_value=120)
if st.sidebar.button("Add Record"):
    new_record = {"id": new_id, "name": new_name, "age": new_age}
    custom_query.add_record(new_record)
    st.sidebar.success("Record added successfully!")

# Update Record Component
st.sidebar.subheader("Update Record")
record_id = st.sidebar.number_input("Enter record ID to update:", min_value=1)
update_name = st.sidebar.text_input("Enter new name:")
update_age = st.sidebar.number_input("Enter new age:", min_value=0, max_value=120)
if st.sidebar.button("Update Record"):
    new_data = {"name": update_name, "age": update_age}
    custom_query.update_record(record_id, new_data)
    st.sidebar.success("Record updated successfully!")

# Delete Record Component
st.sidebar.subheader("Delete Record")
delete_id = st.sidebar.number_input("Enter record ID to delete:", min_value=1)
if st.sidebar.button("Delete Record"):
    custom_query.delete_record(delete_id)
    st.sidebar.success("Record deleted successfully!")

# Read Records Component
st.sidebar.subheader("Read Records")
if st.sidebar.button("Read Database"):
    data = custom_query.read_database()
    st.sidebar.write(data)

# Display the current database
st.header("Current Database")
data = custom_query.read_database()
st.write(data)
