from fastapi import APIRouter, Depends, HTTPException, Security
from app import db, utils
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from app.utils import SECRET_KEY

#OAuth2PasswordBearer - tells where the token should go. it should go to login page
#OAuth2PasswordRequestForm - form data input fetches username and password from ui
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

api = APIRouter(prefix='/auth', tags=['Authentication'])
eng, db_session = db.get_connection()

# dependency injection functions waits for token from oauth2_scheme = login page

def get_current_user(tkn:str = Depends(oauth2_scheme)):
    try:
        decode_tkn = jwt.decode(tkn, key=SECRET_KEY, algorithms=['HS256'])
        username = decode_tkn.get('sub', None)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {'username': username, 'role': f'{decode_tkn.get('role')}'}
    except JWTError as err:
        print(f"JWT Decode Error: {err}")  # This will tell you WHY it's unauthorized


class RoleChecker:
    def __init__(self, allowed_roles:list):
        self.allowed_roles = allowed_roles

    def __call__(self, tkn = Depends(get_current_user)):
        name = tkn.get('username', None)
        role = tkn.get('role', None)

        if role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden action. You do not have permission to perform this action")
        return name




@api.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with db_session() as ss:
        user_exists = utils.get_user(name=form_data.username)

        if not user_exists or not utils.verify_password(form_data.username, form_data.password):
            raise HTTPException(status_code=401, detail="Incorrect username or password") # invalid authentication

        access_token = utils.create_jwt_token(payload = {'sub': user_exists.username,
                                                         'role': f'{utils.get_role_value(user_exists.role_id)}'
                                                         })
        log_params = {'action': 'login', 'entity_type': 'login',
                      'details': f'Login success - {form_data.username}', 'username':form_data.username}
        utils.update_log_table(log_params)
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }




@api.get('/users/me')
def read_me(current_user:dict = Depends(get_current_user)):
    return {'Message':f'{current_user["username"]} authorized. He has following access - {current_user["role"]}'}
