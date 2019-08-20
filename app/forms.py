from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User
from numpy import array
from app.math_tools import points_from_string_list


class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign in")


class AddStepForm(FlaskForm):
    # needs to be able to validate that the min and max values are good
    instrument = SelectField("Instrument Name : ", choices=[("", ""), ], validators=[DataRequired()])
    param = SelectField("Parameter to Adjust : ", choices=[("", ""), ])
    scan_values = StringField("values", validators=[DataRequired()], default='start,stop,numPts;')
    log_spacing = RadioField("Point Spacing", validators=[DataRequired()],
                             choices=[('lin', "lin"), ('log', "log")], default="lin")
    submit = SubmitField('Add Step')
    inst_dict = {}
    processed_vals: array

    def get_instruments(self, all_insts: dict) -> None:
        self.inst_dict = all_insts
        for k in all_insts.keys():
            self.instrument.choices.append([k, k])
        #     for param_name, param_obj in inst_obj.parameters.items():
        #         self.instrument.choices.append([param_name, param_name])
        #         self.param_max[inst_name] = inst_obj.hi_lim
        #         self.param_min[inst_name] = inst_obj.lo_lim
        # # todo generalise minmax for other params

    def step_info(self):
        return (self.instrument.data,
                self.param.data,
                self.processed_vals)

    def prepare_for_validation(self):
        if self.instrument.data != 'None':
            inst = self.instrument.data
            selected_inst = self.inst_dict[inst]
            self.param.choices = [(k, k) for k in selected_inst.keys()]
        else:
            print("no inst!")

    def validate_scan_values(self, field):
        try:
            # converts raw input to np array and checks all within param lims
            data_pts = self._raw_values_to_array(field, sep=";")
            [param_min, param_max] = self._get_selected_param_lims()

            self._check_vals_within_lims(param_min, param_max, data_pts)
            self.processed_vals = data_pts
            return True
        except ValidationError:
            return False


    def _get_selected_param_lims(self):
        inst = self.instrument.data
        param = self.param.data
        selected_param = self.inst_dict[inst][param]
        return selected_param['min_val'], selected_param['max_val']

    def _raw_values_to_array(self, field, sep: str) -> array:
        field.data = field.data.strip().strip(sep)
        log_space = True if self.log_spacing.data == "log" else False
        data_pts = points_from_string_list(field.data, sep=sep,
                                           log=log_space)
        return data_pts

    @staticmethod
    def _check_vals_within_lims(param_min, param_max,  data_pts):
        if data_pts.min() < param_min:
            raise ValidationError(f"values '{data_pts.min()}' less than inst min ({param_min})")
        if data_pts.max() > param_max:
            raise ValidationError(f"values '{data_pts.max()}' greater than inst max ({param_max})")


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    @staticmethod
    def validate_username(username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username is already in use!')

    @staticmethod
    def validate_email(email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
