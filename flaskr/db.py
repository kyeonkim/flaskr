import sqlite3

import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect( # g는 전역 객체로서, 여러 함수에서 공유하는 데이터를 담는데 사용
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES # SQLite 에게 파이썬 타입을 사용하여 컬럼의 데이터를 변환하도록 지시
        )
        g.db.row_factory = sqlite3.Row # row_factory 는 쿼리를 실행한 후에 결과를 어떻게 반환할지를 결정하는 함수
        return g.db

def close_db(e=None):
    db = g.pop('db',None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f: # open_resource() 는 flask가 flaskr 패키지를 어디에 설치했는지를 알고 있음
        db.executescript(f.read().decode('utf8')) # read() 는 파일의 내용을 바이트 문자열로 반환, decode() 는 바이트 문자열을 문자열로 변환

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app): # 함수는 앱의 팩토리 함수에서 호출되어 앱을 전달받음
    app.teardown_appcontext(close_db) # teardown_appcontext() 는 응답이 완료될 때 실행할 함수를 앱에 알림
    app.cli.add_command(init_db_command) # cli.add_command() 는 새로운 명령을 flask 명령에 추가