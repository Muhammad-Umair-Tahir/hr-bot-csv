# HR Bot with CSV Upload Functionality

This project contains a simplified version of an HR bot with CSV upload capabilities. It allows you to:

1. Use an AI-powered HR assistant bot for answering HR policy questions
2. Upload CSV/Excel files containing employee data for bulk processing
3. Connect to a PostgreSQL database for data storage

## Features

- **HR Bot**: Uses Google's Gemini AI and RAG (Retrieval Augmented Generation) with Qdrant vector database
- **CSV Upload**: Upload CSV/Excel files containing employee data
- **Database Integration**: Store employee data in PostgreSQL

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure your environment variables by creating a `.env` file:
   ```
   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/your_database

   # Gemini AI Configuration
   GEMINI_API_KEY=your_gemini_api_key

   # Qdrant Vector Database Configuration
   QDRANT_URL=https://your-qdrant-instance.qdrant.tech
   QDRANT_API_KEY=your_qdrant_api_key
   ```

3. Run the application:
   ```
   uvicorn main:app --reload
   ```

## API Endpoints

- **HR Bot**: `POST /api/v1/chat`
  - Request body: `{"role": "user", "message": "Your question", "session_id": "optional-session-id"}`
  - Response: `{"role": "AI", "message": "Bot response"}`

- **CSV Upload**: `POST /upload-csv/`
  - Form data: `file` (CSV or Excel file)
  - Response: JSON with upload status and results

## Database Models

The application uses the following main models:
- `Person`: Basic employee information
- `Faculty`: Faculty-specific details
- `Designation`: Academic/administrative designations
- `Qualification`: Educational qualifications

## CSV Format Requirements

Your CSV/Excel file should contain columns for:
- Employee Name (will be split into First/Last name)
- Father's Name / Husband's Name
- Sex
- Email
- CNIC #
- CNIC Expiry Date
- Date of Birth
- Mobile #
- Blood Group
- Marital Status
- No Of Dependents
- Date of Marriage
- Title
- Academic Designation
- Administrative Designation
- Code
- Status
- Date of Joining

The uploader contains robust data cleaning pipelines that will attempt to standardize and clean the data.
