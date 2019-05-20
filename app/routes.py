from app import app, db, stages
from quart import render_template, redirect, flash, request, url_for
import trio
from app.mock_objs import mock_xps
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse


@app.route("/", methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
async def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm(await request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            await flash(f"invalid username or password")
            return redirect(url_for("login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('user_home', reuqested_username=current_user.username)
        return redirect(next_page)
    return await render_template('login.html', title="Sign In", form=form)


@app.route("/logout")
@login_required
async def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/index")
@login_required
async def index():
    await trio.sleep(0)
    return await render_template("index.html", title="home")


@app.route("/user/<reuqested_username>")
@login_required
async def user_home(reuqested_username):
    user = User.query.filter_by(username=reuqested_username).first_or_404()
    posts = [
                {"author": user, "body": "test post 1"},
                {"author": user, "body": "test post 2"}
            ]
    return await render_template('user.html', title=user, user=user, posts=posts)


@app.route("/xps")
@login_required
async def xps_view():
    xps = mock_xps
    return await render_template("xps_status.html", title="XPS", xps=xps, stages=list(stages.values()))


@app.route("/scan")
@login_required
async def scan_window():
    return await render_template("scan.html", title="Scan Window", stages=list(stages.values()))


@app.route("/register_user", methods=["GET", "POST"])
@login_required
async def register_user():
    form = RegistrationForm(await request.form)
    if form.validate_on_submit():
        print(form.username.data, form.email.data)
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        await flash(f"New User '{new_user.username}' Added Sucessfully")
        return redirect(url_for("index"))
    return await render_template('register.html', title="Register", form=form)


