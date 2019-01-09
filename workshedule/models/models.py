# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

# re_timeperiod = re.compile("^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")
from odoo.exceptions import UserError

TIMEFORMAT="%H:%M"
weekliststr = "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
weeklist = weekliststr.split(",")

class Timeperiods:

    def __init__(self, ):
        self.b1 = 0
        self.e1 = 0
        self.b2 = 0
        self.e2 = 0

    def to_string(self):
        return ','.join((str(self.b1), str(self.e1), str(self.b2), str(self.e2)))

    def _from_shedule(self, workhours, lunch):
        try:
            d0 = datetime.strptime("00:00", TIMEFORMAT)
            d1, d4 = workhours.split('-')
            d1 = datetime.strptime(d1, TIMEFORMAT)
            if d4 == "24:00":
                d4 = d0 + timedelta(days=1)
            else:
                d4 = datetime.strptime(d4, TIMEFORMAT)
            if d1 >= d4:
                raise UserError("Incorrect period")
            if not lunch:
                self.b1 = int((d1 - d0).total_seconds()/60)
                self.e1 = int((d4 - d0).total_seconds()/60)
                return
            d2, d3 = lunch.split('-')
            d2 = datetime.strptime(d2, TIMEFORMAT)
            d3 = datetime.strptime(d3, TIMEFORMAT)
            if d2 >= d3:
                raise UserError("Incorrect period")
            if d2 <= d1:
                raise UserError("Incorrect period")
            if d3 >= d4:
                raise UserError("Incorrect period")
            self.b1 = int((d1 - d0).total_seconds() / 60)
            self.e1 = int((d2 - d0).total_seconds() / 60)
            self.b2 = int((d3 - d0).total_seconds() / 60)
            self.e2 = int((d4 - d0).total_seconds() / 60)
        except ValueError as e:
            raise UserError(str(e))


    @classmethod
    def from_string(cls, val):
        c = cls()
        c.b1, c.e1, c.b2, c.e2 = val.split(',')
        c.b1, c.e1, c.b2, c.e2 = int(c.b1), int(c.e1), int(c.b2), int(c.e2)
        return c

    @classmethod
    def from_shedule(cls, workhours, lunch):
        c = cls()
        c._from_shedule(workhours, lunch)
        return c

    def align2shedule(self, deadline):
        minutes = deadline.hour * 60 + deadline.minute
        if minutes >= 0 and minutes < self.b1:
            return deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b1)
        elif minutes >= self.b1 and minutes < self.e1:
            return deadline
        elif self.b2 and minutes >= self.e1 and minutes < self.b2:
            return deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b2)
        elif self.b2 and minutes >= self.b2 and minutes < self.e2:
            return deadline
        return deadline.replace(hour=0, minute=0) + timedelta(days=1)

    def _shift_deadline(self, deadline, duration, b, e):
        shift = min(duration, e - b)
        duration -= shift
        deadline += timedelta(minutes=shift)
        return deadline, duration

    def shift_deadline_start(self, deadline, duration):
        dm = deadline.hour * 60 + deadline.minute
        if dm < self.b1:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b1)
            dm = self.b1

        if dm < self.e1:
            deadline, duration = self._shift_deadline(deadline, duration, dm, self.e1)
            dm = self.e1

        if self.b2 and dm < self.b2 and duration:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b2)
            dm = self.b2

        if self.e2 and dm < self.e2 and duration:
            deadline, duration = self._shift_deadline(deadline, duration, dm, self.e2)

        if duration:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(days=1)
        return deadline, duration

    def shift_deadline_next(self, deadline, duration):
        assert duration
        assert (deadline.hour * 60 + deadline.minute) == 0

        deadline = deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b1)
        deadline, duration = self._shift_deadline(deadline, duration, self.b1, self.e1)

        if duration:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b2)
            deadline, duration = self._shift_deadline(deadline, duration, self.b2, self.e2)

        if duration:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(days=1)

        return deadline, duration

    def shift_deadline(self, deadline, duration):
        dm = deadline.hour * 60 + deadline.minute
        if dm < self.e1:
            shift = min(duration, self.e1 - dm)
            duration -= shift
            deadline += timedelta(minutes=shift)
        else:
            pass
        if duration and self.b2:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(minutes=self.b2)
            shift = min(duration, self.e2 - self.b2)
            duration -= shift
            deadline += timedelta(minutes=shift)
        if duration:
            deadline = deadline.replace(hour=0, minute=0) + timedelta(days=1)
        return deadline, duration


class Workhours(models.Model):
    _name = 'workshedule.workhours'

    name = fields.Char("Name", required=True)
    workdays = fields.Char("Work days", default=weekliststr, required=True)
    workhours = fields.Char("Work hours", default="00:00-24:00", required=True)
    lunch = fields.Char("Lunch")
    use_holidays = fields.Boolean("Use Holidays")
    periods = fields.Char(compute='_compute_periods', store=True)

    @api.depends('workhours', 'lunch')
    def _compute_periods(self):
        for rec in self:
            rec.periods = Timeperiods.from_shedule(self.workhours, self.lunch).to_string()

    def isworkingday(self, dt):
        # dt = datetime.date(dt)
        sdt = fields.Date.to_string(dt)
        day = self.env['workshedule.holidays'].search([('date', '=', sdt)])
        if day:
            return day.working
        if weeklist[dt.weekday()] in self.workdays.split(','):
            return True
        return False

    @api.multi
    def get_deadline(self, start, duration):
        self.ensure_one()
        tp = Timeperiods.from_string(self.periods)
        # deadline = tp.align2shedule(start)
        deadline, duration = tp.shift_deadline_start(start, duration)
        while duration:
            if self.isworkingday(deadline):
                deadline, duration = tp.shift_deadline_next(deadline, duration)
            else:
                deadline = deadline.replace(hour=0, minute=0) + timedelta(days=1)
        return deadline

    @api.multi
    def get_timeseries(self, start, duration):
        pass


class Holidays(models.Model):
    _name = 'workshedule.holidays'

    name = fields.Char("Name")
    date = fields.Date("Date")
    working = fields.Boolean("Is working")

# class workshedule(models.Model):
#     _name = 'workshedule.workshedule'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
