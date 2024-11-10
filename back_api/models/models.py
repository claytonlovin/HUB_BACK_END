from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from config.configdb import Base

class Organizacao(Base):
    __tablename__ = 'TB_ORGANIZACAO'
    ID_ORGANIZACAO = Column(Integer, primary_key=True)
    NOME_ORGANIZACAO = Column(String(100), nullable=False)
    DS_CNPJ = Column(String(45), nullable=False, unique=True)
    DATA_CRIACAO = Column(DateTime, nullable=False)
    FL_ATIVO = Column(Boolean)
    PREMIUM = Column(Boolean)
    #users = relationship('User', back_populates='organization')
    grupo_usuario = relationship('GroupUser', back_populates='organizacao')

class User(Base):
    __tablename__ = 'TB_USUARIO'
    ID_USUARIO = Column(Integer, primary_key=True)
    NOME_USUARIO = Column(String(100))
    DS_TELEFONE = Column(String(100))
    DS_EMAIL = Column(String(15))
    DS_LOGIN = Column(String(100))
    DS_SENHA = Column(String(256))
    FL_ADMINISTRADOR = Column(Boolean)
    ID_ORGANIZACAO = Column(Integer, ForeignKey('TB_ORGANIZACAO.ID_ORGANIZACAO'))
    FL_PROPRIETARIO_CONTA = Column(Boolean)
    
    
    #organization = relationship('Organizacao', back_populates='users')
    grupo_usuario = relationship('GroupUser', back_populates='user')

    def __iter__(self):
        return iter((self.ID_USUARIO, self.NOME_USUARIO, self.DS_EMAIL, self.DS_SENHA))

class Grupo(Base):
    __tablename__ = 'TB_GRUPO'
    ID_GRUPO = Column(Integer, primary_key=True)
    NOME_DO_GRUPO = Column(String(500), nullable=False)
    DATA_CRIACAO = Column(DateTime, nullable=False)
    FL_ATIVO = Column(Boolean)
    ID_ORGANIZACAO = Column(Integer, ForeignKey('TB_ORGANIZACAO.ID_ORGANIZACAO'), nullable=False)
    
    
    grupo_usuario = relationship('GroupUser', back_populates='grupo')


class GroupUser(Base):
    __tablename__ = 'TB_GRUPO_USUARIO'
    ID_GRUPO_USUARIO = Column(Integer, primary_key=True)
    ID_GRUPO = Column(Integer, ForeignKey('TB_GRUPO.ID_GRUPO'), nullable=False)
    ID_USUARIO = Column(Integer, ForeignKey('TB_USUARIO.ID_USUARIO'), nullable=False)
    ID_ORGANIZACAO = Column(Integer, ForeignKey('TB_ORGANIZACAO.ID_ORGANIZACAO'), nullable=False)
    
    
    grupo = relationship('Grupo', back_populates='grupo_usuario')
    organizacao = relationship('Organizacao', back_populates='grupo_usuario')
    user = relationship('User', back_populates='grupo_usuario')

    def __iter__(self):
        return iter((self.ID_ORGANIZACAO, self.ID_GRUPO, self.ID_GRUPO_USUARIO, self.ID_USUARIO)) 
    
class Relatorio(Base):
    __tablename__ = 'TB_RELATORIO'
    ID_RELATORIO = Column(Integer, primary_key=True)
    DS_NOME_RELATORIO = Column(String(100), nullable=False)
    DS_LINK_RELATORIO = Column(String(1024), nullable=False)
    ID_GRUPO = Column(Integer, ForeignKey('TB_GRUPO.ID_GRUPO'), nullable=False)


class TypeDatabase(Base):
    __tablename__ = 'TB_TYPE_DATABASE'
    ID_TYPE_DATABASE = Column(Integer, primary_key=True)
    NAME_DATABASE = Column(String(100), nullable=False)

class Database(Base):
    __tablename__ = 'TB_DATABASE'
    ID_DATABASE = Column(Integer, primary_key=True)
    ID_GRUPO = Column(Integer, ForeignKey('TB_GRUPO.ID_GRUPO'), nullable=False)
    IP_CONNECTION = Column(String(100), nullable=False)
    PORT_CONNECTION = Column(String(100), nullable=False)
    USER_CONNECTION = Column(String(100), nullable=False)
    PASSWORD_CONNECTION = Column(String(100), nullable=False)
    DB_CONNECTION = Column(String(100), nullable=False)
    ID_TYPE_DATABASE = Column(Integer, ForeignKey('TB_TYPE_DATABASE.ID_TYPE_DATABASE'), nullable=False)
    def to_dict(self):
        return {
            'ID_DATABASE': self.ID_DATABASE,
            'ID_GRUPO': self.ID_GRUPO,
            'IP_CONNECTION': self.IP_CONNECTION,
            'PORT_CONNECTION': self.PORT_CONNECTION,
            'USER_CONNECTION': self.USER_CONNECTION,
            'PASSWORD_CONNECTION': self.PASSWORD_CONNECTION,
            'DB_CONNECTION': self.DB_CONNECTION,
            'ID_TYPE_DATABASE': self.ID_TYPE_DATABASE
        }
    
