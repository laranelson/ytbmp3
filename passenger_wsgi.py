import sys
import os

# Adiciona o diretório do projeto ao sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Importa a função create_app para criar a instância da aplicação
from app import create_app

# Cria a aplicação e a torna disponível como 'application'
application = create_app()
