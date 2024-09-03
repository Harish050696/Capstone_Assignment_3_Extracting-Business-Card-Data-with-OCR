
# Importing Necessary Libraries

import streamlit as st # Used for creating the web application.
import bcrypt # Used for hashing passwords securely.
import mysql.connector # Used to connect and interact with a MySQL database.
from mysql.connector import Error
from PIL import Image # Used for image processing.
import easyocr #An OCR tool to extract text from images.
import io #Handles byte streams for image data.

# Set page configuration
# Configures the Streamlit page with a title, icon, and layout.

st.set_page_config(page_title="Business Card OCR Application", page_icon=':credit_card:', layout="wide")

# Hide Streamlit components
# Hides the Streamlit menu and footer.

hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Function to create user database, table, and add initial users
# Connects to SQL Server, Creates database user_data and also table users with columns id, name, username, password
def create_user_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="*********"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS user_data")
            cursor.execute("USE user_data")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    username VARCHAR(255) UNIQUE,
                    password TEXT
                )
            """)
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Function to initialize users
# Inserts initial users into the database.
def initialize_users(conn):
    users_to_add = [
        ('Harish', 'hari', 'abc123'),
        ('Wilsto', 'will', 'bro123'),
        ('Harisa', 'wife', 'luv123')
    ]
    
    cursor = conn.cursor()
    for user in users_to_add:
        name, username, password = user
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("""
                INSERT INTO users (name, username, password)
                VALUES (%s, %s, %s)
            """, (name, username, hashed_password))
    
    conn.commit()
    st.success("Users added successfully in the database!")

# Function to authenticate user
# Authenticates the user by checking the username and verifying the hashed password.
def authenticate_user(conn, username, password):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return user['name']
    return None

# Function to preprocess and process image
# Loads the OCR reader and reads the text from the image.
# io functions converts the image to byte data for storing in the database.
def process_image(image):
    reader = load_ocr_reader()
    img = Image.open(image)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    result = reader.readtext(img_bytes, detail=0)
    extracted_text = ' '.join(result)
    return extracted_text, img_bytes

# Function to save extracted text and image to database
# Checks if the extracted text already exists in the database. if not, saves the extracted text and image data to the cards table.
def save_to_database(conn, extracted_text, image_data):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE extracted_text = %s", (extracted_text,))
    existing_record = cursor.fetchone()

    if existing_record:
        st.warning("This record is already in the database!")
    else:
        cursor.execute("""
            INSERT INTO cards (extracted_text, image)
            VALUES (%s, %s)
        """, (extracted_text, image_data))
        conn.commit()
        st.success("Information and image saved to database!")

# Function to fetch all data from the database
# Fetches all data from the cards table.
def fetch_all_data(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cards")
    return cursor.fetchall()

# Function to delete a specific record by ID
# Deletes the record with the specified ID from the cards table.
def delete_record(conn, record_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id=%s", (record_id,))
    conn.commit()

# Function to cache the OCR reader
# Caches the OCR reader to avoid reloading it multiple times, improving performance.
@st.cache_data
def load_ocr_reader():
    return easyocr.Reader(['en'])

# Initialize user database and connection if not already done
# The user database is initialized only once and that the database connection is stored in the session state for future use.
# It also allows for reusing the existing connection if the database has already been initialized.
if 'user_database_initialized' not in st.session_state:
    user_conn = create_user_database()
    if user_conn:
        initialize_users(user_conn)
        st.session_state['user_database_initialized'] = True
        st.session_state['user_conn'] = user_conn
else:
    user_conn = st.session_state['user_conn']

# Create card database and connect to it
def create_card_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="********"
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS business_cards")
            cursor.execute("USE business_cards")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    extracted_text TEXT,
                    image LONGBLOB
                )
            """)
            conn.commit()
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

if 'card_database_conn' not in st.session_state:
    st.session_state['card_database_conn'] = create_card_database()

# Streamlit application layout
st.title("Business Card OCR Application")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    # Authentication section
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        name = authenticate_user(user_conn, username, password)
        if name:
            st.session_state['logged_in'] = True
            st.session_state['name'] = name
            st.success(f"Welcome {name}!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
else:
    # OCR and Database functionality
    st.subheader(f"Welcome {st.session_state['name']}!", divider = True)
    
    uploaded_file = st.file_uploader("Upload a business card image", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
        if st.button("Extract Information"):
            with st.spinner("Processing..."):
                extracted_text, image_data = process_image(uploaded_file)
                save_to_database(st.session_state['card_database_conn'], extracted_text, image_data)

    if st.checkbox("Show all stored records"):
        data = fetch_all_data(st.session_state['card_database_conn'])
        if data:
            st.write("### Stored Business Cards")
            display_data = [{"id": record['id'], "extracted_text": record['extracted_text']} for record in data]
            st.dataframe(display_data)

            record_ids = [record['id'] for record in data]
            selected_id = st.selectbox("Select an ID", options=record_ids, format_func=lambda x: f"ID {x}", placeholder="Choose an ID")

            if selected_id:
                show_image = st.toggle("Show Image")
                if show_image:
                    selected_record = next(record for record in data if record['id'] == selected_id)
                    img = Image.open(io.BytesIO(selected_record['image']))
                    st.image(img, caption=f'Image for ID {selected_id}', use_column_width=True)

                    st.download_button(
                        label="Download Image",
                        data=selected_record['image'],
                        file_name=f"business_card_{selected_id}.png",
                        mime="image/png"
                    )

                if st.button("Delete Record"):
                    delete_record(st.session_state['card_database_conn'], selected_id)
                    st.success(f"Record {selected_id} deleted successfully!")
                    st.experimental_rerun()
        else:
            st.write("No records found.")
    
    # Logout button at the bottom
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Logout", key="logout"):
        st.session_state['logged_in'] = False
        st.experimental_rerun()
