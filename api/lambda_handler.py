"""Punto de entrada para AWS Lambda: adapta la app FastAPI con Mangum."""

from mangum import Mangum

from api.main import app

handler = Mangum(app)
