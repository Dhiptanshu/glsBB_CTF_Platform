"""
GLS Bug Bounty Platform

Copyright (C) 2026 Dhiptanshu Malik

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the LICENSE file for details.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=True) # Mobile number as password
    role = db.Column(db.String(20), default='user') # 'user' or 'admin'
    is_banned = db.Column(db.Boolean, default=False)
    penalty_points = db.Column(db.Integer, default=0)
    solves = db.relationship('Solve', backref='user', lazy=True)
    hint_unlocks = db.relationship('HintUnlock', backref='user', lazy=True)

    def get_score(self):
        solve_score = sum(solve.challenge.points for solve in self.solves)
        hint_deductions = sum(unlock.challenge.hint_cost for unlock in self.hint_unlocks)
        return solve_score - self.penalty_points - hint_deductions

    def get_last_solve_time(self):
        if not self.solves:
            return datetime.max
        return max(solve.timestamp for solve in self.solves)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.String(500), nullable=True) # External link for the category
    is_public = db.Column(db.Boolean, default=False)
    challenges = db.relationship('Challenge', backref='category', lazy=True)

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    free_hint = db.Column(db.Text, nullable=True)
    flag = db.Column(db.String(150), nullable=False)
    points = db.Column(db.Integer, default=100)
    hint = db.Column(db.Text, nullable=True)
    hint_cost = db.Column(db.Integer, default=25)
    order_index = db.Column(db.Integer, default=0)
    # For chained challenges (e.g., in Website category)
    # If not null, this challenge is locked until prerequisite_id is solved by the user
    prerequisite_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=True)
    
    solves = db.relationship('Solve', backref='challenge', lazy=True)
    stats_hint_unlocks = db.relationship('HintUnlock', backref='challenge', lazy=True)

class Solve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class HintUnlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class GlobalSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=True)

