from http.client import HTTPException

from fastapi import APIRouter, Depends
import schema
import utils
from auth import RoleChecker
from models import Workspaces, Users
import db
from router import helper_functions

router = APIRouter(prefix='/workspace', tags=["Workspace"])

allow_access = RoleChecker(['admin','workspace_creator'])
engine, db_session = db.get_connection()


@router.post('/home/createsapce/{space_name}')
def create_workspace( space_name:str,
                      desc:str,
                      current_user:str = Depends(allow_access)):
    created_by = utils.get_user(current_user).uid
    new_space_param = {'user':current_user, 'name':space_name, 'description':desc, 'created_by':created_by}
    check = helper_functions.create_workspace(new_space_param)
    if check:
        log_params = {'action': 'create_workspace',
                      'entity_type': 'worksapce',
                      'details': f'New workspace created - {space_name}',
                      'username': current_user,
                      }
        utils.update_log_table(log_params=log_params)
        return {'message':'Workspace created successfully'}
    return {'message':'Workspace creation failed',
            'error':f'{check}'}


@router.post('/home/deactivate/{space_name}')
def deactivate_workspace( space_name:str,
                          reason:str,
                          current_user:str = Depends(allow_access)):
    try:
        check = helper_functions.deactivate_space(space_name)
        if check:
            log_params = {'action': 'deactivate_workspace',
                          'entity_type': 'workspace',
                          'details': f'Reason for deactivating workspace - {reason}',
                          'username': current_user}
            utils.update_log_table(log_params=log_params)
            return {'Success':'Workspace deactivated successfully'}
        return {'Failed':f'Workspace deactivation failed. Space {space_name} does not exist or is already deactivated'}
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        print(f'Unexpected error occurred - {err}')
        raise HTTPException(status_code=500, detail="An unexpected error occurred")



@router.post('/home/update/{space_name}')
def update_workspace(space_name:str,
                     user_to_update:str,
                     action:schema.UpdateWorkspaceAction,
                     access_level:schema.WorkspaceAccessLevel,
                     current_user:str = Depends(allow_access)):
    try:
        created_by = utils.get_user(current_user).uid
        if not created_by:
            raise HTTPException(status_code=404, detail="User not found")

        update_params = {'space_name':space_name, 'user':user_to_update,
                         'action': action.value, 'access_level':access_level.value}
        check = helper_functions.update_worksapce(update_params)
        if check:
            log_params = {'action': 'update_workspace',
                          'entity_type': 'worksapce',
                          'details': { "workspace_name": f"{space_name}",
                                       "performed_by": f"{created_by}", "action": f"{action.value.upper()}",
                                       "target_user": f"{user_to_update}",
                                       "access_level": f"{access_level.value}"
                                       },
                          'username': current_user}
            utils.update_log_table(log_params=log_params)
            return {'Success':'Workspace updated successfully'}
        return {'Failed':f'Workspace update failed. Space {space_name} does not exist or is already deactivated'}
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        print(f"Unexpected Error: {err}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


