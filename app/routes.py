from app import app, db, xps1, all_insts, scan
from quart import render_template, redirect, flash, request, url_for
import trio
from app.forms import LoginForm, RegistrationForm, AddStepForm, RemoveStepForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
import json

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


# would be good to generalise this
@app.route("/xps")
@login_required
async def xps_view():
    hostname = xps1.host
    stage_position_info = await xps1.param_query_all('Position', ['parent', 'state', 'Position'])
    print(stage_position_info)
    # need name -> parent, state -> postion.state, position -> val
    return await render_template("xps_status.html", title="XPS", hostname=hostname, stages=stage_position_info)


@app.route("/scan", methods=["GET", "POST"])
@login_required
async def scan_window():
    add_step_form = AddStepForm(await request.form)
    rm_step_form = RemoveStepForm()

    stage_position_info = await xps1.param_query_all('all', ['min_val', 'max_val'])
    add_step_form.get_instruments(stage_position_info)
    add_step_form.prepare_for_validation()

    # print(add_step_form.data)
    #
    # print(f"radio choices : {add_step_form.log_spacing.choices}")
    # print(f"radio data : {add_step_form.log_spacing.data}")
    #
    # print(f"p validate : {add_step_form.param.validate(add_step_form)}")
    # print(f"inst validate : {add_step_form.instrument.validate(add_step_form)}")
    # print(f"radio validate : {add_step_form.log_spacing.validate(add_step_form)}")
    # print(f"vals validate : {add_step_form.scan_values.validate(add_step_form)}")

    if add_step_form.validate_on_submit():
        print("val passed")
        step_data = add_step_form.step_info()
        scan.add_step(*step_data)
        print(f"scanning {scan.steps[-1].inst.name}:{scan.steps[-1].parameter}")
    elif request.method == 'POST':
        print("not validated")
        print(f"p choices : {add_step_form.param.choices}")
        print(f"p data : {add_step_form.param.data}")
        print(add_step_form.errors)

    # todo: rm step does nothing
    rm_step_form.get_steps(len(scan.steps))

    return await render_template("scan_ajax.html", title="Scan Window",
                                 add_form=add_step_form, rm_form=rm_step_form, scan=scan)


@app.route('/_parse_data', methods=['POST'])
@login_required
async def parse_data():
    print("got request")
    meth = request.method
    print(meth)

    data_dict = json.loads(await request.data)
    inst_selected = data_dict['inst']

    if meth == "POST" and inst_selected:
        print(f"inst selected: {inst_selected}")

        inst_obj = all_insts.instruments[inst_selected]
        new_params = {k: k for k in inst_obj.parameters.keys()}
        new_params[""] = ""
    else:
        print("empty")
        new_params = {}
    return json.dumps({"msg_success":True, "new_params":new_params})


@app.route('/_start_stop_scan', methods=['POST'])
@login_required
async def start_stop_scan():
    print("got start/stop")

    data_dict = json.loads(await request.data)
    cmd = data_dict['action']
    reply = {"msg_success": True}
    if cmd == "Start Scan":
        reply['msg'] = "scan in progress..."
        reply["button_text"] = "stop scan"
        app.nursery.start_soon(scan.run)
    else:  # cmd == "stop scan":
        reply['msg'] = "scan stopped"
        reply["button_text"] = "Start Scan"
    await trio.sleep(0.4)
    print(cmd)

    return json.dumps(reply)


@app.route("/scan/rm", methods=["POST"])
@login_required
async def scan_window_rm():
    rm_step_form = RemoveStepForm(await request.form)
    add_step_form = AddStepForm()
    add_step_form.get_instruments(all_insts)
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
