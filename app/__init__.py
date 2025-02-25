from flask import Flask

def create_app():
    app = Flask(__name__)

    # Outras configurações e inicializações podem ir aqui, como Blueprints, extensões, etc.

    return app
