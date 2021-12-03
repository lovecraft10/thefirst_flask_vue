from sqlalchemy import create_engine, Column, MetaData, literal, ForeignKey
from flask import Flask, g, jsonify, make_response, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from passlib.apps import custom_app_context
from sqlalchemy import create_engine, text, Column, Integer, String
import os
from datetime import datetime

'''
登录相关的类
'''
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# r'/*' 是通配符，让本服务器所有的 URL 都允许跨域请求
CORS(app, resources=r'/*')
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                        os.path.join(basedir, 'data.sqlite')

db = SQLAlchemy(app)

auth = HTTPBasicAuth()
CSRF_ENABLED = True
app.debug = True


class JoinInfos(db.Model):
    __tablename__ = 'joininfos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    phone = db.Column(db.String(30))
    profess = db.Column(db.String(64))
    grade = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True)
    group = db.Column(db.String(64))
    power = db.Column(db.Text(2000))
    pub_date = db.Column(db.DateTime, default=datetime.now())

    def to_dict(self):
        columns = self.__table__.columns.keys()
        result = {}
        for key in columns:
            if key == 'tid':
                value = getattr(self, key).strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = getattr(self, key)
            result[key] = value
        return result


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    password = db.Column(db.String(128))

    # 密码加密
    def hash_password(self, password):
        self.password = custom_app_context.encrypt(password)

    # 密码解析
    def verify_password(self, password):
        return custom_app_context.verify(password, self.password)

    # 获取token，有效时间10min
    def generate_auth_token(self, expiration=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    # 解析token，确认登录的用户身份
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        admin = Admin.query.get(data['id'])
        return admin


class Fuel(db.Model):
    __tablename__ = 'B01'
    id = db.Column(db.Integer, primary_key=True)
    VIN = db.Column(db.String(64))
    reportTime = db.Column(db.DateTime)
    IP_VehTotDistance = db.Column(db.Float(64))
    IP_FuelLvlInfo = db.Column(db.INT)
    IP_AvgFuelCons = db.Column(db.Float(64))
    IP_InstFuelCons = db.Column(db.Float(64))
    AccelPedlPosnDiagc = db.Column(db.Float(64))
    EngState = db.Column(db.Float(64))
    AccelPedalPosn = db.Column(db.Float(64))
    VehSpd = db.Column(db.Float(64))
    SysPowerMod = db.Column(db.Integer())
    ACOpenSts = db.Column(db.Integer())
    VehLgtAccel = db.Column(db.Float(64))
    FLTirePress = db.Column(db.Float(64))
    FRTirePress = db.Column(db.Float(64))
    RLTirePress = db.Column(db.Float(64))
    RRTirePress = db.Column(db.Float(64))
    DrvWinPosnSts = db.Column(db.INT)
    DrvSideRearWinPosnSts = db.Column(db.INT)
    PassWinPosnSts = db.Column(db.Integer())
    PassSideRearWinPosnSts = db.Column(db.Integer())
    DrivingModDis = db.Column(db.Integer())
    EngSpd = db.Column(db.Float(64))
    VehLatAccel = db.Column(db.Float(64))
    VehYawRate = db.Column(db.Float(64))
    num = db.Column(db.Integer())
    timestamp = db.Column(db.INT)
    timediff = db.Column(db.Integer())
    E_diff = db.Column(db.INT)
    trip_x = db.Column(db.String(64))
    AvgFuelCons = db.Column(db.Float(64))



