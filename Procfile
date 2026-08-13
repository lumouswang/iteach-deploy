web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
release: cd backend && python -c "from pathlib import Path; print('data files:', list((Path('data')).glob('*.json')))"