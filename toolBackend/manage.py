#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import json
from flask import Flask, g, jsonify, make_response, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
from clickhouse_sqlalchemy import make_session, get_declarative_base

from toolBackend.entiy.carCollection import Doors, Trip
from toolBackend.entiy.Admin import Admin, JoinInfos, Fuel

# from toolBackend.utils.clickhouseUtil import carMap

import folium
from folium.plugins import HeatMap
import pymysql

'''
sqllite的连接配置
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

'''
clickhouse连接配置
'''
conf = {
    "user": "default",
    "password": "Abc123456!",
    "host": "10.255.128.201",
    "port": "8123",
    "db": "default"
}
connection = 'clickhouse://{user}:{password}@{host}:{port}/{db}'.format(**conf)
engine = create_engine(connection)
session = make_session(engine)
metadata = MetaData(bind=engine)
Base = get_declarative_base(metadata=metadata)





# @app.route("/joinus", methods=['POST'])
# def joinus():
#     data = request.get_json(force=True)
#     # data = {'InfoName': '折蓉蓉', 'InfoPho': '13466777707','InfoProfess': '数学学院','InfoCls': '大一','InfoEmail':
#     # '266455@qq.com', 'InfoGroup': ['移动', '运营'], 'InfoPower': '测试'}
#     if data:
#         addGroup = ",".join(data['InfoGroup'])
#         addInfos = JoinInfos(
#             name=data['InfoName'],
#             phone=data['InfoPho'],
#             profess=data['InfoProfess'],
#             grade=data['InfoCls'],
#             email=data['InfoEmail'],
#             group=addGroup,
#             power=data['InfoPower']
#         )
#         db.session.add(addInfos)
#         db.session.commit()
#         return jsonify({"status": True})
#     else:
#         return jsonify({"status": False})


@auth.verify_password
def verify_password(name_or_token, password):
    if not name_or_token:
        return False
    name_or_token = re.sub(r'^"|"$', '', name_or_token)
    admin = Admin.verify_auth_token(name_or_token)
    if not admin:
        admin = Admin.query.filter_by(name=name_or_token).first()
        if not admin or not admin.verify_password(password):
            return False
    g.admin = admin
    return True


@app.route('/api/login', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.admin.generate_auth_token()
    return jsonify({'code': 200, 'msg': "登录成功", 'token': token.decode('ascii'), 'name': g.admin.name})


@app.route('/api/setpwd', methods=['POST'])
@auth.login_required
def set_auth_pwd():
    data = json.loads(str(request.data, encoding="utf-8"))
    admin = Admin.query.filter_by(name=g.admin.name).first()
    if admin and admin.verify_password(data['oldpass']) and data['confirpass'] == data['newpass']:
        admin.hash_password(data['newpass'])
        return jsonify({'code': 200, 'msg': "密码修改成功"})
    else:
        return jsonify({'code': 500, 'msg': "请检查输入"})


@app.route('/api/users/listpage', methods=['GET'])
@auth.login_required
def get_user_list():
    page_size = 4
    page = request.args.get('page', 1, type=int)
    name = request.args.get('name', '')
    query = db.session.query
    if name:
        Infos = query(JoinInfos).filter(
            JoinInfos.name.like('%{}%'.format(name)))
    else:
        Infos = query(JoinInfos)
    total = Infos.count()
    if not page:
        Infos = Infos.all()
    else:
        Infos = Infos.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({
        'code': 200,
        'total': total,
        'page_size': page_size,
        'infos': [u.to_dict() for u in Infos]
    })


@app.route('/api/users/doorpage', methods=['GET'])
@auth.login_required
def get_door_list():
    page_size = 20
    page = request.args.get('page', 1, type=int)
    vin = request.args.get('vin', '')
    query1 = db.session.query
    if vin:
        carDoors = query1(Doors).filter(
            Doors.vin.like('%{}%'.format(vin))
        )
    else:
        carDoors = query1(Doors)
    total = carDoors.count()
    if not page:
        carDoors = carDoors.all()
    else:
        carDoors = carDoors.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({
        'code': 200,
        'total': total,
        'page_size': page_size,
        'infos': [u.to_dict() for u in carDoors]
    })


@app.route('/api/users/trippage', methods=['GET'])
def get_trip_list():
    page_size = 60
    page = request.args.get('page', 1, type=int)
    vin = request.args.get('vin', '')
    query1 = db.session.query
    if vin:
        trips = query1(Trip).filter(
            Trip.vin.like('%{}%'.format(vin))
        )
    else:
        trips = query1(Trip)
    total = trips.count()
    if not page:
        trips = trips.all()
    else:
        trips = trips.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({
        'code': 200,
        'total': total,
        'page_size': page_size,
        'infos': [u.to_dict() for u in trips]
    })


@app.route('/api/user/remove', methods=['GET'])
@auth.login_required
def remove_user():
    remove_id = request.args.get('id', type=int)
    if remove_id:
        remove_info = JoinInfos.query.get_or_404(remove_id)
        db.session.delete(remove_info)
        return jsonify({'code': 200, 'msg': "删除成功"})
    else:
        return jsonify({'code': 500, 'msg': "未知错误"})


@app.route('/api/user/bathremove', methods=['GET'])
@auth.login_required
def bathremove_user():
    remove_ids = request.args.get('ids')
    is_current = False
    if remove_ids:
        for remove_id in remove_ids:
            remove_info = JoinInfos.query.get(remove_id)
            if remove_info:
                is_current = True
                db.session.delete(remove_info)
            else:
                pass
        print(remove_ids, remove_info)
        if is_current:
            return jsonify({'code': 200, 'msg': "删除成功"})
        else:
            return jsonify({'code': 404, 'msg': "请正确选择"})
    else:
        return jsonify({'code': 500, 'msg': "未知错误"})


@app.route('/api/getdrawPieChart', methods=['GET'])
@auth.login_required
def getdrawPieChart():
    query = db.session.query
    Infos = query(JoinInfos)
    total1 = Infos.count()
    data_value1 = [0, 0, 0, 0, 0, 0, 0]  # 和下面组别一一对应
    group_value = ['视觉', '视频', '前端', '办公', '后端', '运营', '移动']
    for info in Infos:
        for num in range(0, 7):
            if group_value[num] in info.group:
                data_value1[num] += 1
            else:
                pass
    return jsonify({'code': 200, 'value': data_value1, 'total': total1})


@app.route('/api/getdrawPieChart1', methods=['GET'])
@auth.login_required
def getdrawPieChart1():
    data_value = [0, 0, 0, 0]  # 和下面组别一一对应
    for driverD, passengerD, rrD, rlD in session.query(Doors.driverD, Doors.passengerD, Doors.rrD, Doors.rlD):
        data_value[0] = data_value[0] + driverD
        data_value[1] = data_value[1] + passengerD
        data_value[2] = data_value[2] + rrD
        data_value[3] = data_value[3] + rlD
    total = data_value[0] + data_value[1] + data_value[2] + data_value[3]
    # query = db.session.query
    # for vin in query(Trip.vin):
    #     print(vin)
    return jsonify({'code': 200, 'value': data_value, 'total': total})


@app.route('/api/getdrawLineChart', methods=['GET'])
@auth.login_required
def getdrawLineChart():
    grade_value = []  # 年级汇总
    profess_value = []  # 学院汇总
    grade_data = {}  # 年级各学院字典
    Infos = JoinInfos.query.all()
    for info in Infos:
        if info.grade not in grade_value:
            grade_value.append(info.grade)
            grade_data[info.grade] = []
        if info.profess not in profess_value:
            profess_value.append(info.profess)
    for grade in grade_value:
        for profess in profess_value:
            grade_data[grade].append(0)
    for info in Infos:
        for grade in grade_value:
            for profess_local_num in range(0, len(profess_value)):
                if info.profess == profess_value[profess_local_num] and info.grade == grade:
                    grade_data[grade][profess_local_num] += 1
                else:
                    pass
    return jsonify({'code': 200, 'profess_value': profess_value, 'grade_value': grade_value, 'grade_data': grade_data})


# @app.route('/api/getdrawLineChart1', methods=['GET'])
# @auth.login_required
# def getdrawLineChart1():
#     fuel_value = []  # 年级汇总
#     time_value = []  # 学院汇总
#     time_fuel = {}  # 年级各学院字典
#     query = db.session.query
#     Fuels = query(Fuel)
#     for fuel in Fuels:
#         time_value.append(fuel.reportTime)
#         time_fuel[fuel.reportTime] = []
#         fuel_value.append(fuel.IP_AvgFuelCons)
#
#     for time in time_value:
#         for fuel in fuel_value:
#             time_fuel[time].append(fuel)
#     print(fuel_value)
#     print(time_value)
#     return jsonify({'code': 200, 'fuel_value': fuel_value, 'time_value': time_value, 'time_fuel': time_fuel})


@app.route('/api/getTimeandFuel', methods=['GET'])
@auth.login_required
def getTimeandFuel():
    query = db.session.query
    # vin = request.args.get('vin', '')
    # query1 = db.session.query
    # if vin:
    #     trips = query1(Trip).filter(
    #         Trip.vin.like('%{}%'.format(vin))
    #     )
    # else:
    #     trips = query1(Trip)
    # total = trips.count()
    # if not page:
    #     trips = trips.all()
    # else:
    #     trips = trips.offset((page - 1) * page_size).limit(page_size).all()
    # Fuels = query(Fuel)
    #################
    # 可以查询不同的行程的数据图，不查询时默认使用trip0
    trip_x = request.args.get('trip_x', '')
    if trip_x:
        list1 = query(Fuel).filter(Fuel.trip_x.like('%{}%'.format(trip_x)))
    else:
        list1 = query(Fuel).filter(Fuel.trip_x.like('%trip0%'))
    list1 = list1.all()
    timeData = []
    fuelData = []
    engspdData = []
    vehspdData = []

    # print(list1.reportTime)
    for fuel in list1:
        timeData.append(fuel.reportTime)
        fuelData.append(fuel.IP_AvgFuelCons)
        engspdData.append(fuel.EngSpd)
        vehspdData.append(fuel.VehSpd)
    # timefuel = timeTOfuel()
    # timeData = timefuel['reportTime']
    # fuelData = timefuel['IP_AvgFuelCons']
    return jsonify({'code': 200, 'reportTime': timeData, 'Fuel': fuelData, 'EngSpd': engspdData, 'VehSpd': vehspdData})


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

#
# @app.route('/api/getCarMap', methods=['GET'])
# @auth.login_required
# def getCarMap():
#     # carvin = request.args.get('carVin', '')
#     df1 = carMap()
#     df2 = df1[['lat', 'lon']]
#     folium_map = folium.Map([22.60205, 114.11663], tiles='OpenStreetMap', zoom_start=12)
#     HeatMap(df2).add_to(folium_map)
#     return folium_map._repr_html_()


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0')
