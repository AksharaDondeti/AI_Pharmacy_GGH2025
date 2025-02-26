# # Necessary imports
# import pytesseract
# from PIL import Image


# # Placeholder Groq class or replace with the actual client you are using
# class Groq:
#     def __init__(self):
#         # Placeholder for actual initialization
#         pass

#     class chat:
#         @staticmethod
#         def completions_create(model, messages):
#             # Simulating model completion behavior for now
#             return {
#                 "choices": [
#                     {
#                         "message": {
#                             "content": "Aspirin is used to reduce fever, pain, and inflammation."
#                         }
#                     }
#                 ]
#             }


# # Define the PharmacistAgent class
# class PharmacistAgent:
#     def __init__(self, client: Groq, system: str = "") -> None:
#         self.client = client
#         self.system = system
#         self.messages: list = []
#         if self.system:
#             self.messages.append({"role": "system", "content": system})

#     def __call__(self, message="", image_path=None):
#         if message:
#             self.messages.append({"role": "user", "content": message})
#         if image_path:
#             extracted_text = self.extract_text_from_image(image_path)
#             self.messages.append({"role": "user", "content": extracted_text})
#         result = self.execute()
#         self.messages.append({"role": "assistant", "content": result})
#         return result

#     def execute(self):
#         # Assuming you're using the 'Groq' client (or replace with relevant client)
#         completion = self.client.chat.completions_create(
#             model="llama3-70b-8192", messages=self.messages
#         )
#         return completion['choices'][0]['message']['content']

#     def extract_text_from_image(self, image_path):
#         # Open image using PIL
#         image = Image.open(image_path)
#         # Use Tesseract to extract text
#         extracted_text = pytesseract.image_to_string(image)
#         return extracted_text.strip()

# # Function to get drug information from a database or API
# def get_drug_information(drug_name: str) -> str:
#     # Placeholder function for drug information retrieval.
#     # Replace this with your actual API call or database integration.
#     drug_info = {
#         "aspirin": "Aspirin is used to reduce fever, pain, and inflammation.",
#         "paracetamol": "Paracetamol is used to treat mild to moderate pain and reduce fever.",
#         "ibuprofen": "Ibuprofen is a nonsteroidal anti-inflammatory drug used to reduce fever and pain.",
#     }
#     return drug_info.get(drug_name.lower(), "Drug information not found.")

# # Define the system prompt for the pharmacist agent
# system_prompt = """
# You are a helpful pharmacist agent. When the user asks about a drug, you will:
# 1. Retrieve the relevant drug information.
# 2. Provide an informative and accurate response.
# 3. If the drug is not found in the database, inform the user accordingly.

# Your available actions are:
# 1. get_drug_information: Search for the drug and provide details.

# Example session:
# Question: What is aspirin used for?
# Thought: I need to find the information for aspirin.
# Action: get_drug_information: Aspirin
# PAUSE
# Observation: Aspirin is used to reduce fever, pain, and inflammation.
# Answer: Aspirin is used to reduce fever, pain, and inflammation.
# """

# # Initialize the PharmacistAgent with the client
# client = Groq()  # Initialize your actual model client or API handler
# pharmacist_agent = PharmacistAgent(client=client, system=system_prompt)

# # # Example conversation with the pharmacist agent using text input
# # result_text = pharmacist_agent("What is aspirin used for?")
# # print(result_text)

# # Example conversation with the pharmacist agent using an image
# # Assuming you have an image of a medical prescription
# image_path = "Images/example.png"  # Replace with the actual path to the image
# result_image = pharmacist_agent(image_path=image_path)
# print(result_image)

###

# import pytesseract
# import psycopg2
# import json
# import re
# from PIL import Image

# # Load Database Configuration
# with open("db_config.json", "r") as file:
#     DB_CONFIG = json.load(file)

# def extract_drug_names(text):
#     """
#     Extracts medicine names from the OCR text while filtering out non-drug text.
#     """
#     # Regex pattern to capture only valid drug names
#     pattern = r"\d+\)\s*(?:TAB|CAP)?\.\s*([A-Za-z\s-]+)"
#     matches = re.findall(pattern, text)

#     print("Raw Extracted Drug Names:", matches)  # Debugging output

#     drug_names = []
#     for match in matches:
#         cleaned_name = clean_drug_name(match)
#         if cleaned_name:  # Ensure we only add valid names
#             drug_names.append(cleaned_name)

#     print("Cleaned Drug Names:", drug_names)  # Debugging output
#     return drug_names

# def clean_drug_name(drug_name):
#     """
#     Cleans drug names by removing unwanted words and fixing formatting.
#     """
#     # Words that should NOT be considered as drug names
#     unwanted_words = {"ind", "abo", "od", "leer", "ing", "advice", "given"}

#     # Split words and filter unwanted terms
#     words = drug_name.split()
#     cleaned_words = [word for word in words if word.lower() not in unwanted_words]

#     # Remove special characters and extra spaces
#     cleaned_name = re.sub(r'[^A-Za-z\s-]', '', " ".join(cleaned_words)).strip()

#     return cleaned_name

# def get_drug_information(drug_name):
#     """
#     Fetches drug information from PostgreSQL with fuzzy matching.
#     """
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         cursor = conn.cursor()

#         # Ensure `pg_trgm` extension is enabled
#         cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

#         # Split multi-word drug names to search each part
#         drug_parts = re.split(r'\s+and\s+|\s*,\s*', drug_name)

#         results = []
#         for part in drug_parts:
#             part = part.strip()
#             if not part:
#                 continue  # Skip empty strings

#             print(f"Querying database for: {part}")  # Debugging output

#             query = """
#                 SELECT drug_name, generic_name, drug_class, indications, dosage_form, strength, route_of_administration
#                 FROM drugs 
#                 WHERE drug_name ILIKE %s
#                 OR SIMILARITY(drug_name::text, %s::text) > 0.7
#                 ORDER BY SIMILARITY(drug_name::text, %s::text) DESC
#                 LIMIT 1;
#             """
#             cursor.execute(query, (f"%{part}%", part, part))
#             result = cursor.fetchone()

#             if result:
#                 results.append(
#                     f"Drug: {result[0]}\nGeneric Name: {result[1]}\nClass: {result[2]}\nIndications: {result[3]}\n"
#                     f"Dosage Form: {result[4]}\nStrength: {result[5]}\nRoute: {result[6]}"
#                 )
#             else:
#                 print(f"Drug not found in DB: {part}")  # Debugging output
#                 results.append(f"{part}: No database record found.")

#         return "\n\n".join(results)

#     except psycopg2.Error as e:
#         return f"Database error: {str(e)}"

#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()

# def process_prescription(image_path):
#     """
#     Extracts text from an image, identifies drug names, and fetches their details.
#     """
#     try:
#         image = Image.open(image_path)
#         extracted_text = pytesseract.image_to_string(image)

#         print("Extracted Text:\n", extracted_text)  # Debugging output

#         drug_names = extract_drug_names(extracted_text)

#         if not drug_names:
#             return "No valid drug names detected."

#         # Fetch details for each drug
#         drug_info_list = [get_drug_information(drug) for drug in drug_names]

#         return "\n\n".join(drug_info_list)

#     except Exception as e:
#         return f"Error processing image: {str(e)}"

# # Example Usage
# image_path = "Images/printed_3.png"
# result = process_prescription(image_path)
# print(result)

# import pytesseract
# import psycopg2
# import json
# import re
# from PIL import Image

# # Load Database Configuration
# with open("db_config.json", "r") as file:
#     DB_CONFIG = json.load(file)

# def extract_drug_names(text):
#     """
#     Extracts medicine names from the OCR text while preserving all words in the drug name.
#     """
#     pattern = r"\d+\)\s*(?:TAB|CAP)?\.\s*([\w\s,]+)"
   
#     matches = re.findall(pattern, text)

#     # Ensure extracted names are cleaned properly
#     drug_names = [match.strip() for match in matches]

#     #print("Extracted Drug Names:", drug_names)  # Debugging output
#     return drug_names

# def get_drug_information(drug_name):
#     """
#     Fetches drug information from PostgreSQL with fuzzy matching.
#     """
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         cursor = conn.cursor()

#         # Ensure `pg_trgm` extension is enabled
#         cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

#         drug_parts = re.split(r'\s+and\s+|\s*,\s*', drug_name)

#         results = []
#         for part in drug_parts:
#             part = part.strip()
#             #print(f"Querying database for: {part}")  # Debugging output

#             query = """
#                 SELECT drug_name, generic_name, drug_class, indications, dosage_form, strength, route_of_administration
#                 FROM drugs 
#                 WHERE drug_name ILIKE %s
#                 OR SIMILARITY(drug_name::text, %s::text) > 0.7
#                 ORDER BY SIMILARITY(drug_name::text, %s::text) DESC
#                 LIMIT 1;
#             """
#             cursor.execute(query, (f"%{part}%", part, part))
#             result = cursor.fetchone()

#             if result:
#                 results.append(
#                     f"Drug: {result[0]}\nGeneric Name: {result[1]}\nClass: {result[2]}\nIndications: {result[3]}\n"
#                     f"Dosage Form: {result[4]}\nStrength: {result[5]}\nRoute: {result[6]}"
#                 )
#             else:
#                 results.append(f"{part}: No database record found.")

#         return "\n\n".join(results)

#     except psycopg2.Error as e:
#         return f"Database error: {str(e)}"

#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()


# def process_prescription(image_path):
#     """
#     Extracts text from an image, identifies drug names, and fetches their details.
#     """
#     try:
#         image = Image.open(image_path)
#         extracted_text = pytesseract.image_to_string(image)

#         #print("Extracted Text:\n", extracted_text)  # Debugging output

#         drug_names = extract_drug_names(extracted_text)

#         if not drug_names:
#             return "No valid drug names detected."

#         # Fetch details for each drug
#         drug_info_list = [get_drug_information(drug) for drug in drug_names]

#         return "\n\n".join(drug_info_list)

#     except Exception as e:
#         return f"Error processing image: {str(e)}"

# # Example Usage
# image_path = "Images/printed_3.png"
# result = process_prescription(image_path)
# print(result)


import pytesseract
import psycopg2
import json
import re
import requests
from PIL import Image

# Load Configuration
with open("db_config.json", "r") as file:
    DB_CONFIG = json.load(file)

with open("groq_config.json", "r") as file:
    GROQ_CONFIG = json.load(file)


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


def ask_groq_api(drug_name):
    """
    Queries the Groq API for additional drug information.
    """
    api_key = GROQ_CONFIG.get("api_key")
    api_url = GROQ_CONFIG.get("api_url")

    if not api_key or not api_url:
        return {"Error": "Groq API configuration is missing."}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Provide medical details about {drug_name}."}],
        "max_tokens": 300,
    }

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response_data = response.json()

        return (
            response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if response.status_code == 200
            else {"Error": f"Groq API Error: {response_data}"}
        )

    except requests.RequestException as e:
        return {"Error": f"Request failed: {str(e)}"}


def process_prescription(image_path):
    """
    Extracts text from an image, identifies drug names, and fetches their details.
    """
    try:
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)

        # Extract drug names
        drug_names = extract_drug_names(extracted_text)

        if not drug_names:
            return {"Error": "No valid drug names detected."}

        # Fetch details for each drug
        drug_info_list = [get_drug_information(drug) for drug in drug_names]

        # Query Groq API only for drugs not found in the database
        groq_responses = {
            drug["Drug"]: ask_groq_api(drug["Drug"])
            for drug in drug_info_list
            if "Message" in drug and "No database record found." in drug["Message"]
        }

        return {"Drugs": drug_info_list, "Groq_Responses": groq_responses}

    except Exception as e:
        return {"Error": f"Error processing image: {str(e)}"}


# Example Usage
image_path = "Images/printed_3.png"
result = process_prescription(image_path)
print(json.dumps(result, indent=4))  # Structured Output
