import streamlit as st
import pytesseract
import psycopg2
import json
import re
import ollama
from PIL import Image

# Load Configuration
with open("db_config.json", "r") as file:
    DB_CONFIG = json.load(file)

def extract_drug_names(text):
    """
    Extracts medicine names from OCR text while preserving full drug names.
    """
    pattern = r"\d+\)\s*(?:TAB|CAP)?\.\s*([\w\s,-]+)"
    matches = re.findall(pattern, text)
    
    drug_names = [match.strip() for match in matches if match.strip()]
    return list(set(drug_names))  # Remove duplicates


def get_drug_information(drug_name):
    """
    Fetches drug details from PostgreSQL using fuzzy matching.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Ensure `pg_trgm` extension is enabled
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

        query = """
            SELECT drug_name, generic_name, drug_class, indications, dosage_form, strength, route_of_administration
            FROM drugs 
            WHERE drug_name ILIKE %s
            OR SIMILARITY(drug_name, %s) > 0.7
            ORDER BY SIMILARITY(drug_name, %s) DESC
            LIMIT 1;
        """
        cursor.execute(query, (f"%{drug_name}%", drug_name, drug_name))
        result = cursor.fetchone()

        return (
            {
                "Drug": result[0],
                "Generic Name": result[1],
                "Class": result[2],
                "Indications": result[3],
                "Dosage Form": result[4],
                "Strength": result[5],
                "Route": result[6],
            }
            if result
            else {"Drug": drug_name, "Message": "No database record found."}
        )

    except psycopg2.Error as e:
        return {"Error": f"Database error: {str(e)}"}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def ask_medllama(drug_name):
    """
    Queries MedLlama2 using Ollama for additional drug information.
    """
    try:
        response = ollama.chat(
            model="medllama2",
            messages=[{"role": "user", "content": f"Provide medical details about {drug_name}."}]
        )
        return response['message']['content'].strip() if 'message' in response else {"Error": "No response from MedLlama"}

    except Exception as e:
        return {"Error": f"Model query failed: {str(e)}"}


def process_prescription(image):
    """
    Extracts text from an image, identifies drug names, and fetches their details.
    """
    try:
        extracted_text = pytesseract.image_to_string(image)

        # Extract drug names
        drug_names = extract_drug_names(extracted_text)

        if not drug_names:
            return {"Error": "No valid drug names detected."}

        # Fetch details for each drug
        drug_info_list = [get_drug_information(drug) for drug in drug_names]

        # Query MedLlama for drugs not found in the database
        medllama_responses = {
            drug["Drug"]: ask_medllama(drug["Drug"])
            for drug in drug_info_list
            if "Message" in drug and "No database record found." in drug["Message"]
        }

        return {"MedLlama_Responses": medllama_responses}

    except Exception as e:
        return {"Error": f"Error processing image: {str(e)}"}


# Streamlit UI
st.title("Prescription Drug Analyzer")
st.write("Upload a prescription image to extract drug details.")

uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Prescription", use_column_width=True)

        result = process_prescription(image)

        if "Error" in result:
            st.error(result["Error"])
        elif "MedLlama_Responses" in result and result["MedLlama_Responses"]:
            st.subheader("Additional Drug Information from MedLlama2")
            for drug, details in result["MedLlama_Responses"].items():
                st.info(f"**{drug}**: {details}")
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
