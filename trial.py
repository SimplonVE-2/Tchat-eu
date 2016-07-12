#!/usr/bin/env python
#coding: utf-8

import rethinkdb as r

from rethinkdb.errors import RqlRuntimeError, RqlDriverError
from flask import Flask, render_template, session, request, abort, g, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

async_mode = None


app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

# rethink config
RDB_HOST = 'localhost'
RDB_PORT = 28015
USER_DB = 'dbchat'


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')
# db setup; only run once
def create_db():
    try:
        r.db(USER_DB).table('utilisateurs').run(g.rdb_conn)
    except:
        r.db_create(USER_DB).run(g.rdb_conn)
        r.db(USER_DB).table_create('utilisateurs').run (g.rdb_conn)

def register():
    r.db(USER_DB).table('utilisateurs').insert({'login': request.form['login1'], 'password': request.form['password1'], 'statut':1}).run(g.rdb_conn)

def register_message():
    r.db(USER_DB).table('mes').insert({'message' : request.form['message1']})

#open connection before each request
@app.before_request
def before_requst():
    try:
        g.rdb_conn = r.connect(RDB_HOST, RDB_PORT, USER_DB)
    except RqlDriverError:
        abort(503, "Database connection could be estblished.")

@app.route('/', methods = ['GET', 'POST'])
def index():
    create_db()
    if request.method == 'GET':
        pass
    elif request.method == 'POST' :
        if request.form['submit'] == 'register':
            register()
            return render_template('index.html')
        elif request.form['submit'] == 'login':
            register()
            return render_template('index2.html')
        else :
            print "blue"
    return render_template('index.html')

@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

# close the connection after each request
@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass

if __name__ == '__main__':
    socketio.run(app, debug=True)
