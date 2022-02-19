# -*- coding: utf-8 -*-
import uuid

import numpy as np
from werkzeug.utils import secure_filename

from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for, render_template, request, session, flash
import json
import sys
import os
import cv2 as cv

from stiching import draw

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only


# Heroku
# from flask_heroku import Heroku
# heroku = Heroku(app)


@app.route('/', methods=['GET'])
def root():
    return render_template("index.html")


# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #
# @app.route('/', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form)
    user = helpers.get_user()
    return render_template('home.html', user=user)


# @app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
# @app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
# @app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['jpeg', 'png', 'jpg']


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'first' not in request.files:
            flash('No first file part')
            return redirect(request.url)
        if 'second' not in request.files:
            flash('No second file part')
            return redirect(request.url)
        first = request.files['first']
        second = request.files['second']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if first.filename == '':
            flash('No selected first file')
            return redirect(request.url)
        if second.filename == '':
            flash('No selected second file')
            return redirect(request.url)
        if second and allowed_file(second.filename) and \
                first and allowed_file(first.filename):
            first = np.fromfile(first, np.uint8)
            first = cv.imdecode(first, cv.IMREAD_COLOR)

            second = np.fromfile(second, np.uint8)
            second = cv.imdecode(second, cv.IMREAD_COLOR)
            dst = draw(first, second)
            name = uuid.uuid4()
            cv.imwrite(f'static/image/{name}.png', dst)
            return redirect(url_for("download", file=name))
    return render_template('upload.html')


@app.route('/download/<file>', methods=['GET'])
def download(file):
    return render_template("download.html", file=file)


# ======== Main ============================================================== #
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host="0.0.0.0")
