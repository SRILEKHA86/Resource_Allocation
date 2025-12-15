from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectMultipleField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    start_time = DateTimeField('Start Time (YYYY-MM-DD HH:MM)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Time (YYYY-MM-DD HH:MM)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    description = TextAreaField('Description')
    resources = SelectMultipleField('Resources', coerce=int)
    submit = SubmitField('Save')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        # start < end and handle equality edge case
        if self.start_time.data >= self.end_time.data:
            self.start_time.errors.append('Start time must be before end time.')
            return False
        return True


class ResourceForm(FlaskForm):
    resource_name = StringField('Name', validators=[DataRequired(), Length(max=255)])
    resource_type = StringField('Type', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Save')


class AllocationForm(FlaskForm):
    event_id = SelectField('Event', coerce=int, validators=[DataRequired()])
    resources = SelectMultipleField('Resources', coerce=int)
    submit = SubmitField('Allocate')


class ReportForm(FlaskForm):
    range_start = DateTimeField('Range Start (YYYY-MM-DD HH:MM)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    range_end = DateTimeField('Range End (YYYY-MM-DD HH:MM)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Run Report')
