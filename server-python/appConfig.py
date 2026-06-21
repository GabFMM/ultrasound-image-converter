from flask import Flask
from flask_caching import Cache

# inicializações
app = Flask(__name__)

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 120 # 2 minutos = 120 segundos
})