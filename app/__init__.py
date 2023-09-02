from flask import Flask
from flask_restx import Api
# from flask_marshmallow import Marshmallow

app = Flask(__name__)

# ma = Marshmallow()
api = Api(app, 
        title='API ChatBot',
        version='v1',
        description='REST Api ChatBot',
        prefix='/api/', doc='/swagger/',
        contact='Paul Cruces Ortega',
        contact_url='https://www.linkedin.com/in/paulcruces/')

from app.chatbot import chatbotRouter