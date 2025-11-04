# Disease ETL Pipeline + Dashboard

### 1. Clone the Repository
git clone https://github.com/yourusername/disease-etl.git
cd disease-etl

### 2. Backend Setup
bash
Copy code
cd backend
python -m venv venv
source venv/bin/activate   # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
Create a .env file:

ini
Copy code
Ask for DELPHI_API_KEY

Then start FastAPI:
bash
Copy code
uvicorn app:app --reload
The backend will run at http://127.0.0.1:8000.

### 3. Frontend Setup
bash
Copy code
cd ../frontend
npm install
npm run dev
