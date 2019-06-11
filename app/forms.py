from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User


class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign in")


class AddStepForm(FlaskForm):
    instrument_name = SelectField("Instrument Name", validators=[DataRequired()])
    adjust = SelectField("Adjust", validators=[DataRequired()], choices=[("Position", "position")])
    start_value = FloatField("Start", validators=[DataRequired()])
    fin_value = FloatField("Final", validators=[DataRequired()])
    num_steps = IntegerField("Steps", validators=[DataRequired()])
    submit = SubmitField('Add Step')

    def get_instruments(self, all_insts:dict):
        self.instrument_name.choices = [(stage, stage) for stage in all_insts.keys()]


class RemoveStepForm(FlaskForm):
    step_number = SelectField("Remove", coerce=str, validators=[DataRequired()])
    submit = SubmitField('Remove Step')

    def get_steps(self, num_steps: int):
        self.step_number.choices = [(str(i), str(i+1)) for i in range(num_steps)]


class ParameterSetForm():
    """ set params ahead of the main scan """
    # would be best to do this dynamically using setattr(self, name, field)


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username is already in use!')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')