import uvicorn

from app.router import helper_functions, auth
from fastapi import APIRouter, Depends
from app import utils
from app import schema
from app import db
from app.router import auth


engine, ses_obj = db.get_connection()

#define permissions
allow_admin = auth.RoleChecker(['admin'])

app = APIRouter(prefix="/users", tags=["users"])


@app.get("/home")
def greet():
    return {'message': 'This is a document reader API'}


@app.post("/home/new_user")
def create_user(username: str,
                key: str,
                email: str,
                role: schema.Role,
                current_user:str = Depends(allow_admin)):
    salt, hash_pass = utils.hash_password(key)
    validate_mail = utils.check_email(email)
    if validate_mail:
        params = {'username':username,'password_hash':hash_pass, 'email':email, 'salt':salt, 'role_id':role.value, 'is_active':1}
        flag= helper_functions.create_user(params)
        if flag:
            # update the activity_log table
            log_params = {'action':'create_user', 'entity_type':'users', 'details':f'New user created - {username}', 'username':username}
            utils.update_log_table(log_params)
            return {'message': 'User created successfully', 'RC':flag}
        return {'message': 'User already exists', 'Error Code': flag}


# update user email, password,
@app.patch("/home/update_mail/{name}/email")
def update_email(name: str, mail: str, current_user:str = Depends(allow_admin)):
    validate_mail = utils.check_email(mail)
    if validate_mail:
        params = {'username': name, 'email': mail, 'passkey':None}
        check = helper_functions.update_user(params)
        if check:
            log_params = {'action':'update_email', 'entity_type':'users', 'details':f'User - {name} updated their email',  'username':name}
            utils.update_log_table(log_params)
            return {'message':'User updated successfully', 'RC':check}
        return {'message': 'Unable to update', 'Error Code': check}



@app.patch("/home/update_key/{name}/passkey")
def update_password(name:str, mail: str, passkey: str):
    validate_email = utils.check_email(mail)
    if validate_email:
        params = {'username': name, 'email': mail, 'passkey':passkey}
        check = helper_functions.update_user(params)
        if check:
            log_params = {'action': 'update_password', 'entity_type': 'users',
                          'details': f'User - {name} updated their password',  'username':name}
            utils.update_log_table(log_params)
            return {'message': 'User updated successfully', 'RC': check}
        return {'message': 'Unable to update', 'Error Code': check}


# active_status - de-active (0)
@app.delete("/home/deactive/{name}")
def delete_user(name: str,email:str, reason:str, current_user = Depends(allow_admin)):
    validate_email = utils.check_email(email)
    if validate_email:
        helper_functions.deactivate_user(name=name, mail=email)
        log_params = {'action': 'delete_user', 'entity_type': 'users',
                      'details': f'User - {name} deactivated. Reason - {reason}',  'username':name}
        utils.update_log_table(log_params)
        return {'message': 'User deactivated successfully', 'RC': reason}
    return {'message':'Error deactivating'}





if __name__ == '__main__':
    uvicorn.run("doc_main:app", host="127.0.0.1", port=8000, reload=True)