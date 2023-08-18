$env:PYTHONIOENCODING = "UTF-8"
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements_cuda.txt 

Start-Process "uvicorn" "opendream.server:app --reload" -NoNewWindow

Set-Location webapp/opendream-ui
npm install
npm run start