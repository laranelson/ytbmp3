import sys
import os

# Adiciona o diretório do projeto ao sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Importa a função create_app
from app import create_app

# Cria a aplicação
application = create_app()  # Agora o Passenger usará a instância `application`
