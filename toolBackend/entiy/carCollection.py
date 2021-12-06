from datetime import datetime
import os
import re
import json
import time
from flask import Flask, g, jsonify, make_response, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from passlib.apps import custom_app_context
from sqlalchemy import create_engine, Column, MetaData, literal, ForeignKey
from clickhouse_sqlalchemy import make_session, get_declarative_base, types, engines
from clickhouse_sqlalchemy import make_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, MetaData, literal, ForeignKey
from sqlalchemy import Table, Column, Integer, String, DateTime, BIGINT, VARCHAR
import sqlalchemy
import pymysql
'''
车联网数据相关的类
'''
conf1 = {
    "user": "root",
    "password": "123456",
    "host": "localhost",
    "port": "3306",
    "db": "car"
}
connection = 'mysql+pymysql://{user}:{password}@{host}:{port}/{db}'.format(**conf1)

engine = create_engine(connection)
session = make_session(engine)
metadata = MetaData(bind=engine)
Base = get_declarative_base(metadata=metadata)


def millisecond_to_time(millis):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(millis / 1000))


# 车门类
class Doors(Base):
    __tablename__ = 'door'
    uid = Column(types.UUID, primary_key=True)
    vin = Column(types.String)
    driverD = Column(types.Int16)
    passengerD = Column(types.Int16)
    rrD = Column(types.Int16)
    rlD = Column(types.Int16)

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            if key == 'tid':
                value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(getattr(self, key) / 1000))
            else:
                value = getattr(self, key)
            result[key] = value
        return result


# 行程类
class Trip(Base):
    __tablename__ = 'tripView'
    uid = Column(types.UUID, primary_key=True)
    vin = Column(types.String)
    tid = Column(types.UInt64)
    time_diff = Column(types.Float64)
    sys_diff = Column(types.Int16)
    win = Column(types.Int16)
    VehTotDistance = Column(types.UInt16)
    tripId = Column(types.UInt64)

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            if key == 'tid':
                value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(getattr(self, key) / 1000))
            else:
                value = getattr(self, key)
            result[key] = value
        return result


class Map(Base):
    __tablename__ = 'tripView1'
    uid = Column(types.UUID, primary_key=True)
    vin = Column(types.String)
    date = Column(types.DateTime64)
    lat = Column(types.Float64)
    lon = Column(types.Float64)
    vehicle_spd = Column(types.Float64)
    eng_spd = Column(types.Float64)
    tripId = Column(types.Int16)


# 借用台账
class StandingBook(Base):
    __tablename__ = 'car_standing_book'
    id = Column(BIGINT, primary_key=True)
    car_id = Column(BIGINT, index=True)
    cyy = Column(VARCHAR(255))
    depart = Column(VARCHAR(255))
    operator = Column(VARCHAR(255))
    mobile_phone = Column(VARCHAR(255))
    project_name = Column(VARCHAR(500))
    begin_date = Column(DateTime)
    end_date = Column(DateTime)
    give_back = Column(Integer())

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            if key == 'tid':
                value = getattr(self, key).strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = getattr(self, key)
            result[key] = str(value)
        return result

# 故障台账
class CarFault(Base):
    __tablename__ = 'car_fault'
    id = Column(BIGINT, primary_key=True)
    car_id = Column(BIGINT, index=True)
    fault_describe = Column(VARCHAR(1000))
    create_by = Column(BIGINT)
    create_time = Column(DateTime)
    update_by = Column(BIGINT)
    update_time = Column(DateTime)

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            if key == 'tid':
                value = getattr(self, key).strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = getattr(self, key)
            result[key] = str(value)
