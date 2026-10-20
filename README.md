
# install_and_run.sh

echo "Instalando RetailMax MVP..."

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt
pip install streamlit

# Inicializar base de datos
cd backend
python seed_data.py
cd ..

echo "Instalación completada"
echo ""
echo " Para ejecutar el MVP:"
echo "1. Backend: cd backend && python main.py"
echo "2. Frontend: cd frontend && python -m http.server 3000"
echo "3. Dashboard: cd dashboard && streamlit run dashboard.py"
echo ""
echo " URLs:"
echo "- Frontend PWA: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- Dashboard: http://localhost:8501"
echo "- API Docs: http://localhost:8000/docs"