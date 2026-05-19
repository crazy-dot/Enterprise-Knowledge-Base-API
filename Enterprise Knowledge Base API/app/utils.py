import os
import hashlib
import secrets
from datetime import datetime, timedelta
import psycopg2
from email_validator import validate_email, EmailNotValidError


from app import db, models
from jose import jwt



SECRET_KEY = ''
ALGORITHM = 'HS256'
ACCESS_EXPIRE_IN_MINS = 30

eng, sess = db.get_connection()

def create_jwt_token(payload: dict) ->  str:
    to_encode = payload.copy() #shallow copy
    expire_mins = datetime.now() + timedelta(minutes=ACCESS_EXPIRE_IN_MINS)
    to_encode.update({'exp': expire_mins})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm='HS256')
    return encoded_jwt


def hash_password(key: str):
    salt = os.urandom(16) # 16 byte binary string
    # sha256 is fast algo will be completed in msecs so more vulnerable. use pbkdf2_hmac method with work flow
    # iterations = 100000 standard. return type - bytes convert to hex and store in db
    hash_object = hashlib.pbkdf2_hmac('sha256', key.encode('utf-8'), salt, iterations=100000)
    return salt.hex(), hash_object.hex()


def check_email(email: str):
    try:
        vmail = validate_email(email, check_deliverability=True)
        normalized_mail = vmail.normalized
        return normalized_mail
    except EmailNotValidError:
        return {'Invaild Email': email}

def update_log_table(log_params:dict):
    with sess() as ss:
        try:
            log_update = models.Activity_logs(user_id = get_user_id_for_log(log_params['username']),
                                              action=log_params['action'],
                                              entity_type=log_params['entity_type'],
                                              details=log_params['details'])
            ss.add(log_update)
            ss.commit()
        except psycopg2.Error as err:
            return err


def verify_password(username:str, passkey: str):
    #rehash the new entered pass and compare using compare_digest()
    with sess() as ss:
        stored_hash = ss.query(models.Users).filter(models.Users.username == username).first()
        if stored_hash is None:
            return False

        stored_salt_bytes = bytes.fromhex(stored_hash.salt)
        stored_password_bytes = bytes.fromhex(stored_hash.password_hash)

        new_hash = hashlib.pbkdf2_hmac('sha256', passkey.encode('utf-8'),
                                       stored_salt_bytes, iterations=100000)

        return secrets.compare_digest(stored_password_bytes, new_hash)




#---------------------------------------simple utilities functions----------------------
def get_role_value(id:int):
    with sess() as ss:
        role = ss.query(models.Roles).filter(models.Roles.id == id).first()
        return role.role_name

def get_role_id(role_value: str):
    with sess() as ss:
        user_role = ss.query(models.Roles).filter(models.Roles.role_name == role_value).first()
        return user_role.id


def get_user_id_for_log(name: str):
    with sess() as ss:
        user_id = ss.query(models.Users).filter(
            models.Users.username == name and models.Users.updated_at == datetime.now()).first()
        return user_id.uid

def get_user(name:str):
    with sess() as ss:
        res = ss.query(models.Users).filter(models.Users.username == name).first()
        return res

def get_pass(name:str):
    with sess() as ss:
        res = ss.query(models.Users).filter(models.Users.username == name).first()
        return

def get_workspace_id(workspace_name: str):
    with sess() as ss:
        res = ss.query(models.Workspaces).filter(models.Workspaces.name == workspace_name).first()
        return res

def workspace_user_details(space_id:int, user_id:int):
    with sess() as ss:
        res = ss.query(models.Workspace_members).filter(models.Workspace_members.user_id == user_id
                                                        and models.Workspace_members.workspace_id == space_id).first()
        return res


