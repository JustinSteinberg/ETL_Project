Date: 2025
Description:
    This project implements a full end-to-end ETL pipeline for
    Influenza-Like Illness (ILI) data from the Carnegie Mellon
    Delphi Epidata API. It fetches weekly flu surveillance data,
    transforms and stores it in SQLite, and visualizes results
    in an interactive web dashboard built with SvelteKit.

--------------------------------------------------------------
 DATA SCHEMA
--------------------------------------------------------------

Columns:
    date        : Monday of ISO week (YYYY-MM-DD)
    region      : Two-letter U.S. state code
    value       : Weighted Influenza-Like Illness (%)
    metric      : “ili”
    source_id   : Unique per (region + epiweek)
    epiweek     : Epidemiological week (YYYYWW)

--------------------------------------------------------------
 SETUP INSTRUCTIONS
--------------------------------------------------------------

1. Clone the repository:
       git clone https://github.com/<your-username>/disease-etl.git
       cd disease-etl

--------------------------------------------------------------
 BACKEND SETUP (FastAPI + SQLite)
--------------------------------------------------------------

2. Enter backend directory:
       cd disease_etl_backend

3. Create a virtual environment:
       python -m venv venv
       source venv/bin/activate        (macOS / Linux)
       venv\Scripts\activate           (Windows)

4. Install dependencies:
       pip install -r requirements.txt

5. Create a `.env` file in backend/:
       DELPHI_API_KEY=your_api_key_here

   (Obtain an API key at: https://cmu-delphi.github.io/delphi-epidata/)

6. Run the FastAPI backend:
       uvicorn app:app --reload

   The API will be available at:
       http://127.0.0.1:8000

--------------------------------------------------------------
 FRONTEND SETUP (SvelteKit)
--------------------------------------------------------------

7. In a new terminal, enter the frontend folder:
       cd ../frontend

8. Install dependencies:
       npm install

9. Start the development server:
       npm run dev

   Access the dashboard at:
       http://localhost:5173

--------------------------------------------------------------
 TESTING
--------------------------------------------------------------

Run unit tests from the backend directory:
       pytest -v

The tests verify:
   • Transform logic and schema integrity
   • SQLite UPSERT and deduplication
   • Summary statistics accuracy
   • API responses (success + failure)
   • Mocked fetch to simulate API errors

--------------------------------------------------------------
 EXAMPLE ENDPOINTS
--------------------------------------------------------------

    POST /etl/run        → Run ETL for date range
    GET  /data           → Retrieve data rows
    GET  /stats          → Summary statistics
    GET  /map            → Mean ILI per state (for heatmap)
    GET  /download.csv   → Download cleaned dataset

--------------------------------------------------------------
 VISUALIZATION FEATURES
--------------------------------------------------------------

   • Interactive line chart of ILI (%) by week
   • Data table view with pagination
   • U.S. heatmap showing ILI intensity per state
   • Summary cards showing min, max, mean, median, stdev
   
   <img width="1056" height="715" alt="Screenshot 2025-11-04 at 6 01 48 PM" src="https://github.com/user-attachments/assets/d3e1cf43-1798-4235-a30a-f951d4610fe4" />


  <img width="1218" height="724" alt="Screenshot 2025-11-04 at 6 01 15 PM" src="https://github.com/user-attachments/assets/0fffe741-83a2-4d68-9f97-343747eaa740" />

--------------------------------------------------------------
 LICENSE
--------------------------------------------------------------

MIT License © 2025 Justin Steinberg  
Based on public data from the Carnegie Mellon University Delphi Group
