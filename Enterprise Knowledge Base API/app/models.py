
from sqlalchemy import  Integer, func, String, DateTime, ForeignKey, Text, BigInteger, Sequence, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from app import db

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'
    uid: Mapped[int] = mapped_column(Integer, Sequence('users_uid_seq', start=100), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    salt: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



class Roles(Base):
    #Stores user access roles
    __tablename__ = 'roles'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name:Mapped[str] = mapped_column(String(255), nullable=False)
    description:Mapped[str] = mapped_column(Text)


class Workspaces(Base):
    __tablename__ = 'workspaces'
    id: Mapped[int] = mapped_column(Integer,Sequence('workspaces_id_seq', start=1), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('users.uid'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Workspace_members(Base):
    #Maps users to workspaces
    __tablename__ = 'workspace_members'
    id:Mapped[int] = mapped_column(Integer,Sequence('wspc_mem_id_seq', start=1), primary_key=True)
    workspace_id:Mapped[int] = mapped_column(Integer, ForeignKey('workspaces.id'))
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey('users.uid'))
    access_level:Mapped[str] = mapped_column(String(50), nullable=False)
    added_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Documents(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey('workspaces.id'))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(BigInteger)
    category: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50))
    uploaded_by: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived_by: Mapped[str] = mapped_column(String(100))
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))



class Document_versions(Base):
    #Tracks document updates
    __tablename__ = 'document_versions'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id:Mapped[int] = mapped_column(Integer, ForeignKey('documents.id'))
    version_number:Mapped[str] = mapped_column(String(50))
    file_path :Mapped[str] = mapped_column(String(255))
    change_note:Mapped[str] = mapped_column(String(255))
    created_by:Mapped[str] = mapped_column(String(100))
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Document_tags(Base):
    __tablename__ = 'document_tags'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id:Mapped[int] = mapped_column(Integer, ForeignKey('documents.id'))
    tag_name:Mapped[str] = mapped_column(String(255))


class Activity_logs(Base):
    __tablename__ = 'activity_logs'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey('users.uid'))
    action:Mapped[str] = mapped_column(String(255))
    entity_type:Mapped[str] = mapped_column(String(255))
    details:Mapped[str] = mapped_column(String(255))
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



if __name__ == '__main__':
    engine, session = db.get_connection()
    Base.metadata.create_all(engine)

    # admin = Roles(id=1, role_name='admin', description='Administrator. Has full access to workspaces, and user management')
    # workspace_creater = Roles(id=2, role_name='workspace_creater', description='can create workspaces.')
    # standard_user = Roles(id=3, role_name='standard_user', description='Admin or owner needs to give access to use workspace.')
    # with Session(engine) as sess:
    #     sess.add_all([admin, workspace_creater, standard_user])
    #     sess.commit()

