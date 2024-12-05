import os 
import bcrypt

from dotenv import load_dotenv

load_dotenv('.env')
groups = ["FWD", "FWS"]


string_password = bcrypt.hashpw(password=os.getenv('SUPER_ADMIN').encode('utf-8'), salt=bcrypt.gensalt()).decode('utf8')

phone = os.getenv('PHONE')

superadmin = {
    'phone': phone,
    'password' : string_password
}

