import os
import json
import requests
from neo4j import GraphDatabase
from rapidfuzz import process as rapid_process
from PIL import Image
import pytesseract
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Neo4j driver setup
driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD))

def get_drug_information_from_neo4j(drug_name):
    """
    Fetches drug details from the Neo4j database using fuzzy matching.
    """
    print(f"Fetching details for drug: {drug_name}")
    with driver.session() as session:
        query = """
        MATCH (m:Medicine {name: $drug_name})-[:HAS_SIDE_EFFECT]->(s:SideEffect),
              (m)-[:MANUFACTURED_BY]->(mf:Manufacturer),
              (m)-[:BELONGS_TO]->(cc:ChemicalClass)
        RETURN m.name AS drug_name, m.composition AS composition, s.name AS side_effects, 
               mf.name AS manufacturer, cc.name AS chemical_class
        LIMIT 1
        """
        result = session.run(query, drug_name=drug_name)
        record = result.single()

        if record:
            print(f"Found drug details for {drug_name}: {record}")
            return {
                "Drug": record["drug_name"],
                "Composition": record["composition"],
                "Side Effects": record["side_effects"],
                "Manufacturer": record["manufacturer"],
                "Chemical Class": record["chemical_class"]
            }
        else:
            print(f"No details found for drug: {drug_name}")
            return {"Drug": drug_name, "Message": "No database record found."}

def extract_drug_names_fuzzy(text, known_drug_list):
    """
    Extracts drug names using fuzzy matching with a known database of drugs.
    """
    print(f"Extracting drug names from the text: {text}")
    extracted_names = text.split()
    matched_drugs = []

    for word in extracted_names:
        result = rapid_process.extractOne(word, known_drug_list)
        if result:
            match, score, *_ = result  # Unpack only needed values
            if score > 75:
                matched_drugs.append(match)

    print(f"Matched drugs: {matched_drugs}")
    return list(set(matched_drugs))  # Remove duplicates

def extract_text(image_path):
    """
    Extracts text from an image using Tesseract OCR.
    """
    print(f"Extracting text from image: {image_path}")
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        print(f"Extracted Text: {text}")
        return text
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""

def structure_answer_with_groq(drug_data):
    """
    Uses Groq API to structure the final drug information into a user-friendly paragraph format.
    If data is fetched from Neo4j, the response will be appropriately mentioned.
    """
    print("Structuring the answer using Groq API")
    with open("groq_config.json", "r") as file:
        GROQ_CONFIG = json.load(file)

    api_key = GROQ_CONFIG.get("api_key")
    api_url = GROQ_CONFIG.get("api_url")

    if not api_key or not api_url:
        print("Groq API configuration is missing.")
        return {"Error": "Groq API configuration is missing."}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Prepare the structured data, clearly stating where the data is coming from
    message_content = f"""
    You are an expert medical AI assistant. Given the following drug details from a Neo4j graph database, provide a well-structured paragraph explanation for each drug. 
    Explain its purpose, how it works, and any important details in natural language. The source of the data is Neo4j, a graph database containing comprehensive information on drugs, their side effects, manufacturers, and chemical classes.

    The drug details are as follows:

    {json.dumps(drug_data, indent=2)}

    If the data is unavailable or the drug is not found, indicate that the information could not be retrieved from the database.
    """

    data = {
        "model": "llama-3.3-70b-versatile",  # Adjust model as needed
        "messages": [{"role": "user", "content": message_content}],
        "max_tokens": 800,  # Adjust depending on expected output length
    }

    try:
        print(f"Making request to Groq API with data: {data}")
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Groq API response: {response.json()}")
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Error response from Groq API: {response.text}")
            return {"Error": response.text}

    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        return {"Error": f"Request failed: {str(e)}"}

def process_prescription(image_path):
    """
    Full pipeline to process a prescription image, extract drugs, fetch medical info from Neo4j, and structure the answer.
    """
    print(f"Processing prescription image: {image_path}")
    # Step 1: Extract text using OCR
    extracted_text = extract_text(image_path)  # Correcting the function call here
    if not extracted_text:
        print("No text extracted from image. Exiting process.")
        return {"Error": "No text extracted from the image."}

    print("Extracted Text:\n", extracted_text)

    # Step 2: Extract drug names (fuzzy matching)
    try:
        with driver.session() as session:
            query = "MATCH (m:Medicine) RETURN m.name"
            known_drug_list = [record["m.name"] for record in session.run(query)]
        print(f"Fetched {len(known_drug_list)} known drugs from Neo4j.")
    except Exception as e:
        print("Error while fetching drug names from Neo4j:", e)
        known_drug_list = []

    drug_names = extract_drug_names_fuzzy(extracted_text, known_drug_list)
    print("Identified Drugs:", drug_names)

    # Step 3: Fetch details for each drug
    final_results = []
    for drug in drug_names:
        drug_info = get_drug_information_from_neo4j(drug)
        final_results.append(drug_info)

    # Step 4: Structure the response using the Groq API
    print("Final drug data for Groq:", final_results)
    structured_answer = structure_answer_with_groq(final_results)
    
    return structured_answer

# Run the full pipeline
image_path = "Images/printed_3.png"
final_output = process_prescription(image_path)
print("Final Structured Output:\n", final_output)
