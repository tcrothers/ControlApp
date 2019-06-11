from app import app, db, stages, scan
from quart import render_template, redirect, flash, request, url_for
import trio
from app.mock_objs import mock_xps
from app.forms import LoginForm, RegistrationForm, AddStepForm, RemoveStepForm
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
            next_page = url_for('user_home', requested_username=current_user.username)
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


@app.route("/user/<requested_username>")
@login_required
async def user_home(requested_username):
    user = User.query.filter_by(username=requested_username).first_or_404()
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


@app.route("/scan/rm", methods=["POST"])
@login_required
async def scan_window_rm():
    rm_step_form = RemoveStepForm(await request.form)
    add_step_form = AddStepForm()
    add_step_form.get_instruments(stages)
    rm_step_form.get_steps(len(scan.steps))

    print("validation", rm_step_form.validate_on_submit())
    print("submitted", rm_step_form.is_submitted())
    print("data", rm_step_form.step_number.data)

    if rm_step_form.validate_on_submit():
        print("rm validated")
        scan.rm_step(rm_step_form)
        rm_step_form.get_steps(len(scan.steps))
    else:
        await flash("validation failed")

    return await render_template("scan.html", title="Scan Window",
                                 add_form=add_step_form, rm_form=rm_step_form, scan=scan)


@app.route("/scan", methods=["GET", "POST"])
@login_required
async def scan_window():
    print("at start of scan window")
    f = await request.form
    print(f)
    add_step_form = AddStepForm(await request.form)
    rm_step_form = RemoveStepForm()

    print("add_form pre validate")
    print(add_step_form.data)


    add_step_form.get_instruments(stages)

    print("add_form post get")
    print(add_step_form.data)

    if add_step_form.validate_on_submit():
        scan.add_step(add_step_form)

    rm_step_form.get_steps(len(scan.steps))

    print(rm_step_form.step_number.choices)
    return await render_template("scan.html", title="Scan Window",
                                 add_form=add_step_form, rm_form=rm_step_form, scan=scan)


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
