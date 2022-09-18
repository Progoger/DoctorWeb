from flask import Flask, render_template, request, send_file, make_response
import Queries
import Constants
import os
import psycopg2
import hashlib
from functools import wraps

conn = psycopg2.connect(database="DoctorWeb", user="postgres",
                        password="postgres", host="localhost", port=5432)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Constants.UPLOAD_FOLDER


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if auth:
            name = auth.username
            pas = auth.password
            sha = hashlib.sha256()
            sha.update(pas.encode())
            cur = conn.cursor()
            cur.execute(Queries.CHECK_USER, {'login': name, 'password': sha.hexdigest()})
            data = cur.fetchall()
            cur.close()
            if data:
                req = f(*args, **kwargs)
                req.set_cookie('id', str(data[0][0]))
                return req
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    return wrapper


@app.route('/')
@auth_required
def main():
    return make_response(render_template('index.html'))


@app.route('/upload')
@auth_required
def upl_file():
    return make_response(render_template('upload.html'))


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        sha = hashlib.sha256()
        while True:
            data = f.read(Constants.BUF_SIZE)
            if not data:
                break
            sha.update(data)
        file_hash = sha.hexdigest()
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])
        directory = app.config['UPLOAD_FOLDER'] + '\\' + file_hash[0:2]
        if not os.path.exists(directory):
            os.mkdir(directory)
        if not os.path.isfile(directory + '\\' + file_hash):
            f.seek(0, 0)
            f.save(os.path.join(directory, file_hash))
            cur = conn.cursor()
            cur.execute(Queries.INSERT_FILE, {'hash': file_hash, 'user_id': request.cookies.get('id')})
            conn.commit()
            cur.close()
            return file_hash+Constants.GO_BACK
        return 'this file is already exists'+Constants.GO_BACK


@app.route('/delete')
@auth_required
def delete():
    return make_response(render_template('delete.html'))


@app.route('/deleter', methods=['GET', 'POST'])
def deleter():
    if request.method == 'POST':
        f = request.form['file']
        directory = app.config['UPLOAD_FOLDER'] + '\\' + f[0:2]
        if os.path.isdir(directory) and os.path.isfile(directory + '\\' + f):
            cur = conn.cursor()
            cur.execute(Queries.CHECK_FILE, {'hash': f, 'user_id': request.cookies.get('id')})
            if cur.fetchall():
                os.remove(app.config['UPLOAD_FOLDER'] + '\\' + f[0:2] + '\\' + f)
                cur.close()
                return 'Deleted'+Constants.GO_BACK
            else:
                cur.close()
                return 'You are not the owner'+Constants.GO_BACK

    return 'Not such a file'+Constants.GO_BACK


@app.route('/download')
@auth_required
def download():
    return make_response(render_template('download.html'))


@app.route('/downloader', methods=['GET', 'POST'])
def downloader():
    if request.method == 'POST':
        f = request.form['file']
        directory = app.config['UPLOAD_FOLDER'] + '\\' + f[0:2]
        if os.path.isdir(directory) and os.path.isfile(directory + '\\' + f):
            return send_file(app.config['UPLOAD_FOLDER'] + '\\' + f[0:2] + '\\' + f, as_attachment=True)
    return 'not such a file'+Constants.GO_BACK


if __name__ == '__main__':
    app.run(debug=True)
