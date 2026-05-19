"""
script for validation - we define via pydantic model
enum model for role selection
"""
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class Role(Enum):
    admin = 'admin'
    workspace_creator = 'workspace_creator'
    standard_user = 'standard_user'

class UpdateWorkspaceAction(Enum):
    add = 'add'
    remove = 'remove'
    update = 'update'

class WorkspaceAccessLevel(Enum):
    owner = 'owner'
    editor = 'editor'
    member = 'member'
    viewer = 'viewer'

#editior can edit existing document, member can upload new document or simply view - no edit option
#viewer - can only view

class Users(BaseModel):
    uid: str
    username: str = Field(..., description='username', min_length=3, max_length=20)
    salt: str
    password_hash: str = Field(..., min_length=5)
    email: str = Field(..., description='email')
    role_id: int
    is_active: int
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime


class Roles(BaseModel):
    id: int
    role_name:str
    description:str


class Workspaces(BaseModel):
    id: int
    name: str
    description: str
    created_by: str
    is_active: int
    created_at: datetime
    updated_at: datetime

class Workspace_members(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    access_level: str
    added_at: datetime


class Documents(BaseModel):
    id: int
    workspace_id :int
    title: str
    description: str
    file_name: str
    file_path: str
    file_type: str
    file_size: str
    category: str
    status: str
    uploaded_by: str
    created_at : datetime
    updated_at: datetime


class Document_versions(BaseModel):
    id: int
    document_id: int
    version_number: str
    file_path : str
    change_note: str
    created_by: str
    created_at: datetime


class Document_tags(BaseModel):
    id: int
    document_id: int
    tag_name: str

class Activity_logs(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: str
    details: str
    created_at:datetime