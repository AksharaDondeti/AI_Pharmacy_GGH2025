# AI_Pharmacy_GGH2025
# AI Pharma - Prescription Analyzer

## Overview
AI Pharma is a prescription analysis system that leverages OCR, LLM-powered retrieval, and a PostgreSQL drug database to extract and retrieve accurate drug information. The system supports printed and, in later versions, handwritten prescriptions.

## Features
- **OCR-based Prescription Analysis**: Uses Tesseract to extract text from prescription images.
- **Drug Database Integration**: Retrieves structured drug data from PostgreSQL.
- **LLM-powered Pharmacist Agent**: Uses an LLM to provide contextual drug information.
- **Retrieval-Augmented Generation (RAG)**: Enhances drug-related queries with structured and unstructured data.
- **Secure and Scalable**: Future enhancements include encryption, RBAC, and compliance with HIPAA/GDPR.

## Getting Started
### Prerequisites
Ensure you have the following installed:
- Python 3.x
- PostgreSQL
- Tesseract OCR
- Required Python dependencies (see `requirements.txt`)

### Setup Instructions
1. Clone the repository:
   ```sh
   git clone https://github.com/AksharaDondeti/AI_Pharmacy_GGH2025.git
   cd AI_Pharmacy_GGH2025
   
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure database settings in `db_config.json`.
4. Run the Streamlit application:
   ```sh
   streamlit run app.py
   ```

## Design Idea and Approach
The AI Pharma system combines an LLM-powered pharmacist agent with a PostgreSQL drug database, Tesseract OCR for prescription scanning, and a Retrieval-Augmented Generation (RAG) model for accurate drug information retrieval.

- **Version 1** establishes structured data storage, intelligent querying, and OCR for printed prescriptions.
- **Version 2** expands capabilities with a CNN model for handwritten prescription recognition and a graph database for dynamic drug interaction analysis.

Planned enhancements include robust security measures such as data encryption, role-based access control (RBAC), and compliance with HIPAA/GDPR to safeguard sensitive information. Designed for scalability, the system ensures efficient, low-latency responses while maintaining strict privacy standards, optimizing pharmaceutical assistance with greater accuracy and reliability.


## Acknowledgments
Special thanks to the open-source community and medical data providers that contribute to improving AI-driven healthcare solutions.

##The submitted proposal represents the overall plan, while the linked Git repository includes partial implementations of several modules. Development is ongoing, with continuous efforts to refine and expand the system.

