from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class Event(db.Model):
    __tablename__ = 'events'
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, default='')

    allocations = db.relationship('EventResourceAllocation', back_populates='event', cascade='all, delete-orphan')


class Resource(db.Model):
    __tablename__ = 'resources'
    resource_id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(255), nullable=False, unique=True)
    resource_type = db.Column(db.String(64), nullable=False)

    allocations = db.relationship('EventResourceAllocation', back_populates='resource', cascade='all, delete-orphan')


class EventResourceAllocation(db.Model):
    __tablename__ = 'event_resource_allocations'
    allocation_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), nullable=False, index=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.resource_id'), nullable=False, index=True)

    event = db.relationship('Event', back_populates='allocations')
    resource = db.relationship('Resource', back_populates='allocations')

    __table_args__ = (
        db.UniqueConstraint('event_id', 'resource_id', name='uq_event_resource'),
    )
