import sys
import os

# Adiciona o diretório do projeto ao sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Importa a aplicação Flask
from app import app as application  # Passenger exige que a variável se chame `application`
