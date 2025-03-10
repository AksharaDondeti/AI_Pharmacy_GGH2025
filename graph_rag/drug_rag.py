import streamlit as st
import pytesseract
import re
from PIL import Image
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD))

# Stopwords list (used only for filtering, NOT querying)
STOPWORDS = {
    "and", "or", "with", "mixed", "tablet", "capsule", "solution",
    "cream", "ointment", "mg", "ml", "injection", "syrup", "for", "of",
    "the", "a", "an", "to", "from", "on", "at", "by", "as", "this",
    "that", "it", "is", "are", "was", "were", "be", "been", "being",
    "which", "who", "whom", "whose", "there", "their", "they", "them"
}

# Function to clean extracted drug names
def clean_drug_name(drug_name):
    drug_name = drug_name.lower()
    drug_name = re.sub(r'[^a-zA-Z0-9 ]', '', drug_name).strip()
    filtered_drug_words = [word for word in drug_name.split() if word not in STOPWORDS]
    return filtered_drug_words

# Function to extract drug names from OCR text
def extract_drug_names(text):
    pattern = r"\d+\)\s*(?:TAB|CAP)?\.\s*([\w\s,-]+)"
    matches = re.findall(pattern, text)
    
    drug_names = [match.strip() for match in matches if match.strip()]
    return list(set(drug_names))  # Remove duplicates

# Query function for a single drug (checking both name and composition)
def query_single_drug(tx, drug_name):
    query = """
    MATCH (d:Medicine)
    WHERE toLower(d.name) CONTAINS toLower($drug_name) 
       OR toLower(d.composition) CONTAINS toLower($drug_name)
    
    OPTIONAL MATCH (d)-[:TREATS]->(u:UseCase)
    OPTIONAL MATCH (d)-[:HAS_SIDE_EFFECT]->(s:SideEffect)
    OPTIONAL MATCH (d)-[:MANUFACTURED_BY]->(mf:Manufacturer)
    OPTIONAL MATCH (d)-[:HAS_SUBSTITUTE]->(sub:Substitute)

    RETURN 
        $drug_name AS ExtractedDrug,
        COLLECT(DISTINCT d.name) AS Medicines, 
        COLLECT(DISTINCT d.composition) AS Compositions, 
        COLLECT(DISTINCT u.name) AS Uses, 
        COLLECT(DISTINCT s.name) AS SideEffects, 
        COLLECT(DISTINCT mf.name) AS Manufacturers, 
        COLLECT(DISTINCT sub.name) AS Substitutes
    """
    return tx.run(query, drug_name=drug_name).single()

# Streamlit UI setup
st.title("Drug Information Extraction")

# Sidebar for page navigation
page = st.sidebar.selectbox("Select a Page", ["About", "Upload Prescription"])

if page == "About":
    st.header("About This App")
    st.write("""
        This app allows users to extract and retrieve drug information such as medicines, compositions, uses, side effects,
        manufacturers, and substitutes from medical prescriptions using OCR technology and a connected Neo4j graph database.
        Simply upload an image of a prescription, and the app will extract drug names and provide additional information.
    """)

elif page == "Upload Prescription":
    st.header("Upload Prescription Image")

    # Upload file
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Use pytesseract to extract text from the image
        image = Image.open(uploaded_file)
        extracted_text = pytesseract.image_to_string(image)

        # Extract drug names from the OCR text
        drug_names = extract_drug_names(extracted_text)

        # Clean and process the drug names
        processed_drugs = set()
        for drug in drug_names:
            cleaned_drug_parts = clean_drug_name(drug)
            processed_drugs.update(cleaned_drug_parts)

        # Query Neo4j for each drug and display the results
        result = {}
        with driver.session() as session:
            for drug in processed_drugs:
                record = session.execute_read(query_single_drug, drug)
                if record:
                    drug_info = {
                        "Medicines": record["Medicines"],
                        "Compositions": record["Compositions"],
                        "Uses": record["Uses"] if record["Uses"] else "N/A",
                        "SideEffects": record["SideEffects"] if record["SideEffects"] else "N/A",
                        "Manufacturers": record["Manufacturers"] if record["Manufacturers"] else "N/A",
                        "Substitutes": record["Substitutes"] if record["Substitutes"] else "N/A"
                    }
                else:
                    drug_info = {"Error": "No data found"}
                result[drug] = drug_info

        # Display results
        st.write("### Extracted Drug Information")
        st.json(result)
