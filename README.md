Capstone Assignment 3: Business Card Data Extraction with OCR

This Streamlit application extracts text from business cards using OCR and stores the text and image in a SQL database. The application features:

User Authentication

- User database and table creation with id, name, username, and password columns
- Initialization of users with hashed passwords
- Username and password verification for authentication

OCR and Database Functionality

- Business card image upload
- Text extraction from images using OCR
- Storage of extracted text and image data in the database
- Display of stored records with image viewing and deletion options

Database Connection

- Connection to MySQL database
- Storage of connection in session state for future use

Streamlit Application Layout

- Login form for user authentication
- Business card image upload form
- Display of extracted text and images
- Options to view and delete stored records
- Logout button

Functions

- create_user_database(): Creates user database and table
- initialize_users(): Initializes users with hashed passwords
- authenticate_user(): Authenticates users by verifying username and password
- process_image(): Extracts text from images using OCR
- save_to_database(): Saves extracted text and image data to database
- fetch_all_data(): Fetches all stored records from database
- delete_record(): Deletes record from database by ID
- load_ocr_reader(): Caches OCR reader for improved performance
