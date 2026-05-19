from datetime import timezone, datetime

import psycopg2
from app.db import get_connection
from app.models import *
from app import utils
from fastapi import HTTPException


engine, db_session = get_connection()


def create_user(userparams: dict):
    with db_session() as ss:
        try:
            insert = Users(username=userparams['username'], salt=userparams['salt'], password_hash=userparams['password_hash'],
                           email=userparams['email'], role_id= utils.get_role_id(userparams['role_id']),
                           is_active=userparams['is_active'])
            ss.add(insert)
            ss.commit()
            return 1
        except psycopg2.Error as err:
            print(err)
            raise HTTPException(status_code=500, detail='Database Error')


def update_user(params: dict):
    with db_session() as ss:
        try:
            usercheck = ss.query(Users).filter(Users.username == params['username'], Users.is_active ==1).first()
            if usercheck and len(params['email']) !=0 and params['passkey'] is None:
                usercheck.email = params['email']
                ss.commit()
                return 1

            if usercheck and params['passkey'] is not None:
                user_to_modify = ss.query(Users).filter(Users.username == params['username'],Users.email == params['email'],Users.is_active ==1).first()
                msalt, mhash = utils.hash_password(params['passkey'])
                user_to_modify.salt = msalt
                user_to_modify.password_hash = mhash
                ss.commit()
                return 1

        except psycopg2.Error as err:
            print(err)
            raise HTTPException(status_code=500, detail='Database Error')


def deactivate_user(name: str, mail:str):
    with db_session() as ss:
        try:
            usercheck = ss.query(Users).filter(Users.username == name, Users.email == mail).first()
            if usercheck:
                usercheck.is_active = 0
                ss.commit()
                return 1
        except psycopg2.Error as err:
            print(err)
            raise HTTPException(status_code=500, detail='Database Error')



def create_workspace(params: dict):
    # params - user, name, description, created_by
    try:
        with db_session() as ss:
            new_wkspc = Workspaces(name=params.get('name'),
                               description=params.get('description'),
                               created_by=params.get('created_by'))
            ss.add(new_wkspc)
            ss.flush() # moves changes to db but doesn't commit - save pending
            new_member = Workspace_members(workspace_id=new_wkspc.id,
                                           user_id=params.get('created_by'),
                                           access_level= "owner")
            ss.add(new_member)
            ss.commit()
            return 1
    except psycopg2.Error as err:
        print(err)
        raise HTTPException(status_code=500, detail='Database Error')


def update_worksapce(params: dict):
    # params = {'space_name', 'user', 'action to be taken - add/remove',access_level - owner, editor or viewer
    try:
        with db_session() as ss:
            wkspc = ss.query(Workspaces).filter(Workspaces.name == params.get('space_name'), Workspaces.is_active ==1).first()
            # workspace like this doesn't exist or deactivated
            if not wkspc:
                return 0

            # fetch user id from users table. If user doesn't exist raise exception
            update_user_id = ss.query(Users.uid).filter(Users.username == params.get('user')).scalar()
            if not update_user_id:
                raise HTTPException(status_code=404, detail='User does not exist')


            if params.get('action') == 'add':
                add_member = Workspace_members(workspace_id=wkspc.id,
                                               user_id=update_user_id,
                                               access_level=params.get('access_level'))
                ss.add(add_member)
                ss.commit()
                return 1 # non-zero code success

            member_check = ss.query(Workspace_members).filter(Workspace_members.workspace_id == wkspc.id,
                                                              Workspace_members.user_id == update_user_id).first()
            if not member_check:
                return 0 # no such user to delete in this workspace

            if params.get('action') == 'remove':
                ss.delete(member_check)
                ss.commit()
                return 1

            if params.get('action') =='update':
                member_check.access_level = params.get('access_level')
                ss.commit()
                return 1
    except psycopg2.IntegrityError: #Bad request
        ss.rollback()
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    except psycopg2.Error as err: #5x series - debug backend
        print(err)
        raise HTTPException(status_code=500, detail="Internal Server Error")




def deactivate_space(space_name:str):
    try:
        with db_session() as ss:
            wkspc = ss.query(Workspaces).filter(Workspaces.name == space_name).first()
            if wkspc.name is not None or wkspc.is_active!=0:
                wkspc.is_active = 0
                ss.commit()
                return 1
            return 0
    except psycopg2.Error as err:
        print (err)
        raise HTTPException(status_code=404, detail="Workspace does not exist")


def create_document(params:dict):
    try:
        with db_session() as ss:
            doc = Documents(workspace_id=params.get('workspace_id'),title=params.get('title'),description=params.get('description'),
                            file_name=params.get('file_name'),file_path=params.get('file_path'),file_type=params.get('file_type'),
                            file_size=params.get('file_size'),category=params.get('category'),status=params.get('status'),
                            uploaded_by=params.get('uploaded_by'))
            ss.add(doc)
            ss.flush()
            doc_version = Document_versions(document_id=doc.id, version_number=params.get('version'),file_path=params.get('file_path'),
                                            change_note="new document upload",created_by=params.get('uploaded_by')
                                            )
            ss.add(doc_version)
            ss.flush()
            doc_tag = Document_tags(document_id=doc.id,tag_name=params.get('tags'))
            ss.add(doc_tag)
            ss.commit()
    except psycopg2.Error as err:
        print(err)
        raise HTTPException(status_code=500, detail="Database Error")

def update_document(params:dict):
    try:
        with db_session() as ss:
            doc_details = ss.query(Documents).filter(Documents.workspace_id == params.get('space_id'),Documents.file_name == params.get('file_name')).first()
            if doc_details is None:
                raise HTTPException(status_code=404, detail="Document details does not exist in db. Table update failed")

            doc_details.file_size = params.get('file_size')
            doc_details.uploaded_by = params.get('uploaded_by')
            doc_details.status = params.get('status')
            doc_details.version = params.get('version')
            ss.flush()

            doc_version = Document_versions(document_id=doc_details.id, version_number=params.get('version'),
                                            file_path=params.get('file_path'),
                                            change_note=params.get('change_note'), created_by=params.get('uploaded_by')
                                            )
            ss.add(doc_version)
            ss.flush()

            doc_tags = ss.query(Document_tags).filter(Document_tags.document_id == doc_details.document_id).first()
            doc_tags.tag_name = params.get('tags') if params.get('tags') is not None else doc_tags.tags

            ss.commit()

    except psycopg2.Error as err:
        print(err)
        raise HTTPException(status_code=500, detail="Database Error")


def delete_document(params:dict):
    try:
        with db_session() as ss:
            doc = ss.query(Documents).filter(Documents.workspace_id == params.get('space_id'),Documents.file_name == params.get('file_name')).first()
            if doc is None:
                raise HTTPException(status_code=404, detail="Document details does not exist in db. Table update failed")

            doc.status = params.get('status')
            doc.archived_by = params.get('archived_by')
            doc.archived_at = datetime.now(timezone.utc) # automatically convert to local timezone on querying
    except psycopg2.Error as err:
        print(err)
        raise HTTPException(status_code=500, detail="Database Error")

def list_documents(params:dict):
    try:
        with db_session() as ss:
            doc_list = ss.query(Documents.file_name).filter(Documents.workspace_id == params.get('space_id'),
                                                            Documents.status != 'archived').all()
            if doc_list is None:
                return 0
            data = doc_list
            return data
    except psycopg2.Error as err:
        print(err)
        raise HTTPException(status_code=500, detail="Database Error")









if __name__ =='__main__':
    print("Welcome")
    engine, sesobj = get_connection()