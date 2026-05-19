from pathlib import  Path

from anyio.streams import file
from fastapi import APIRouter,HTTPException, UploadFile, Depends, Form, File
from db import get_connection
from router.auth import RoleChecker
import utils
import helper_functions


allow_access = RoleChecker(['admin','workspace_creator', 'standard_user'])
read_access = ['owner','editor','member','viewer']
upload_access = ['owner','editor','member']
update_access = ['owner','editor']
delete_access = ['owner'] #doc owner can delete

allowed_extensions = ['application/pdf','text/plain','application/json',
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

router = APIRouter(prefix='/documents', tags=['Documents'])
eng,db_session = get_connection()

BASE_DIR = Path(__file__).resolve().parent.parent.parent  #router>app>LLM
UPLOAD_DIR = BASE_DIR / "files"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)



def verify_access(space_id:int, current_user:str, action:str=None):
    # get access level for this user
    current_user_id = utils.get_user_id_for_log(current_user)
    user_details = utils.workspace_user_details(space_id=space_id, user_id=current_user_id)

    if user_details.user_id is None:
        raise HTTPException(status_code=404, detail='User not found in this workspace')

    if action =='upload' and user_details.access_level not in update_access: # create new
        raise HTTPException(status_code=403,detail="Access denied")
    if action =='update' and user_details.access_level not in update_access: # modifying the existing
        raise HTTPException(status_code=403,detail="Access denied")
    if action =='delete' and user_details.access_level not in delete_access:
        raise HTTPException(status_code=403,detail="Access denied")
    return 1


"""create a directory for each workspace and uplaod document makes sure no duplicates are
present. If we use a single directory the original will be overwritten (mode = wb).
if mode = xb is used exclusive write makes sure to throw error"""

@router.post('/home/upload_document')
async def upload_document(file: UploadFile = File(...),
                    workspace_name:str = Form(...),
                    desc: str|None = Form(None),
                    file_category:str|None = Form(None),
                    version:int|None = Form(None),
                    tags: str|None = Form(None),
                    current_user = Depends(allow_access)):
    try:
        # 1. get workspace_id - db check
        wkspc = utils.get_workspace_id(workspace_name)
        if wkspc is None:
            raise HTTPException(status_code=404,detail="Workspace not found")
        # 2. access verification and content check
        verify_access(wkspc.id, current_user, action='upload')

        if file.content_type not in allowed_extensions:
            raise HTTPException(status_code=400,detail="File type not supported")
        # 3. create local repository
        workspace_dir = UPLOAD_DIR/str(wkspc.name)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        # 4. write file contents to local
        file_path = workspace_dir / str(file.filename)
        with open(file_path,'xb') as f:
            while chunks:= await file.read(1024*1024):
                f.write(chunks)

        # 5. update db -
        db_params = {'workspace_id':wkspc.id, 'title':Path(file_path).stem, 'description':desc, 'file_name':file.filename,
                     'file_path':str(file_path), 'file_type':file.content_type, 'category': file_category, 'status':'active', 'version':version,
                     'file_size': file.size/1024, 'uploaded_by': current_user, 'tags':tags
                     }
        helper_functions.create_document(db_params)
        log_params = {'action': 'create/uplaod document', 'entity_type': 'documents',
                      'details': f'Document uploaded - {file.filename}',
                      'username': current_user,
                      }
        utils.update_log_table(log_params)
        return {'message':'File upload success'}
    except HTTPException as http_err:
        raise http_err
    except FileExistsError as err:
        raise HTTPException(status_code=400,detail=str(err)) # wrong input
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500,detail='Unexpected Error') # unexpected error - debug code


"""check if workspace and file exists. then update"""

@router.post('/home/{workspace}/{document_name}')
async def update_document(file:UploadFile = File(...),
                    workspace_name:str = Form(...),
                    version: str|None = Form(None),
                    tags:str|None = Form(None),
                    change_note:str|None = Form(None),
                    current_user = Depends(allow_access)):
    """check if workspace and file exists. then update"""
    try:
        wkspc = utils.get_workspace_id(workspace_name)
        if wkspc is None:
            raise HTTPException(status_code=404, detail='Workspace not found')

        # 1. Workspace check in the local repository
        file_check = Path(UPLOAD_DIR/str(workspace_name)/str(file.filename))
        print(file_check)
        if not file_check.exists():
            raise HTTPException(status_code=404,detail="File or Workspace not found in the repository")

        # 2. access verification and content verification
        verify_access(wkspc.id, current_user, action='update')

        if file.content_type not in allowed_extensions:
            raise HTTPException(status_code=400, detail="File type not supported")

        # 3. overwrite existing file
        with open(file_check, 'wb') as f:
            while chunks := await file.read(1024 * 1024):
                f.write(chunks)

        db_params = {'file_size': file.size/1024, 'uploaded_by': current_user, 'space_id':wkspc.id,
                     'file_name': file.filename, 'version':version, 'tags':tags, 'status':'updated', 'change_note':change_note}
        helper_functions.update_document(db_params)
        log_params = {'action': 'update document', 'entity_type': 'documents',
                      'details': f'Updated Document {file.filename} by user - {current_user}','username': current_user,
                      }
        utils.update_log_table(log_params)
        return {'message':'File updated success'}

    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500,detail='Unexpected Error')

"""Do not move files when archiving. Simply update the document status to archived and hide archived documents from normal queries"""
@router.delete('/home/{document_name')
def delete_document(workspace_name:str,
                    document_name:str,
                    current_user:str = Depends(allow_access)):
    try:
        wkspc = utils.get_workspace_id(workspace_name)
        # 1. workspace and document check
        space_check = Path(UPLOAD_DIR/str(workspace_name))
        if not space_check.exists():
            raise HTTPException(status_code=404,detail="Workspace not found")
        file_check = Path(space_check/str(document_name))
        if not file_check.exists():
            raise HTTPException(status_code=404,detail=f"{document_name} not found in the workspace - {workspace_name}")

        # 2. verify access
        verify_access(wkspc.id, current_user,action='delete')

        # 3. remove document - change status to archive. let the document be in the same place
        db_params = {'status':'archived','archived_by':current_user, 'space_id':wkspc.id, 'file_name':document_name}
        helper_functions.update_document(db_params)
        log_params = {'action': 'archived document', 'entity_type': 'documents',
                      'details': f'User {current_user} deleted document - {document_name}', 'username': current_user,
                      }
        utils.update_log_table(log_params)
        return {'message':'Deleted document successfully'}

    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        print(err)
        raise HTTPException(status_code=500,detail='Unexpected Error')



@router.get('/home/list_documents')
def list_documents(workspace_name:str):
    wkspc = utils.get_workspace_id(workspace_name)
    params = {'space_name':workspace_name, 'space_id':wkspc.id}
    check = helper_functions.list_documents(params)
    if check ==0:
        return {'message':'No documents found '}
    return check
