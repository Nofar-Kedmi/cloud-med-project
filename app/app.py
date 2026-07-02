from app import create_app

# Vercel צריך אובייקט בשם 'app' כדי להריץ את ה-Serverless Function
app = create_app()