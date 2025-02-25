import sys
import os

# Adiciona o diretório do projeto ao sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Imprimir sys.path para depuração
print(sys.path)

# Importa a função create_app de app/__init__.py
from app import create_app

# Cria a aplicação
application = create_app()

