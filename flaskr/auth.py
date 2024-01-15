import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
# Blueprint 는 라우트, 템플릿, 정적 파일 등을 담고 있는 뷰의 집합
bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    # 데코레이터는 함수를 수정하지 않고 기능을 추가할 수 있음
    # 데코레이터는 뷰 함수를 감싸고, 뷰 함수가 실행되기 전에 먼저 실행됨
    # 데코레이터는 새로운 함수를 반환하거나, 기존의 함수를 변경해서 반환함
    # functools.wraps 데코레이터는 적용된 원본 뷰를 래핑하는 새로운 뷰 함수를 반환
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login')) # url_for() 는 뷰 이름과 인수를 받아서 해당하는 URL을 반환
        return view(**kwargs)
    return wrapped_view

@bp.before_app_request # before_app_request 는 뷰가 실행되기 전에 실행되는 함수를 등록
def load_logged_in_user():
    # session 에 user_id 가 있는지 확인하고, 그렇지 않으면 g.user 를 None 으로 설정
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        # g.user 는 get_db() 를 호출하고 사용자 정보를 db에서 가져온 뒤 저장
        g.user = get_db().execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()

# url_prefix 는 블루프린트에 등록된 모든 뷰의 URL 앞에 붙는다.
# 예를 들어 auth.bp 는 /register 를 /auth/register 로 바꾼다.
@bp.route('/register', methods=('GET','POST'))
def register():
    # request.method 는 사용자가 브라우저에 URL을 입력해서 요청을 보낼 때 사용된 메서드
    if request.method == 'POST':
        # request.form은 사용자가 폼에 제출한 데이터에 접근할 수 있게 해주는 특수한 딕셔너리
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username: # username 이 없으면 에러
            error = 'Username is required.'
        elif not password: # password 가 없으면 에러
            error = 'Password is required.'
        
        if error is None:
            try:
                # db.execute() 는 SQL 쿼리를 실행하고 결과를 반환
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?,?)",
                    (username, generate_password_hash(password))
                )
                db.commit()
            except db.IntegrityError:
                # IntegrityError 는 UNIQUE 제약 조건에 위배되는 경우 발생
                error = f"User {username} is already registered."
            else:
                # url_for() 는 뷰 이름과 인수를 받아서 해당하는 URL을 반환
                return redirect(url_for('auth.login'))
        # flash() 는 다음 요청까지 메시지를 저장
        flash(error)
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db=get_db()
        error = None
        # fetchone() 은 쿼리 결과에서 한 줄을 반환
        # 쿼리 결과가 없으면 None을 반환
        # fetchall() 은 쿼리 결과에서 모든 줄을 반환
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user['password'],password):
            error = "Incorrect password."
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
    flash(error)

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))