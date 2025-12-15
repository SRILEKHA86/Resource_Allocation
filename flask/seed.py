from app import app
from models import db, Resource, Event, EventResourceAllocation
from datetime import datetime, timedelta

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create resources
    r1 = Resource(resource_name='Room A', resource_type='room')
    r2 = Resource(resource_name='Room B', resource_type='room')
    r3 = Resource(resource_name='Projector 1', resource_type='equipment')
    r4 = Resource(resource_name='Alice', resource_type='instructor')
    db.session.add_all([r1, r2, r3, r4])
    db.session.commit()

    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    e1 = Event(title='Workshop 101', start_time=base + timedelta(hours=1), end_time=base + timedelta(hours=3), description='Intro')
    e2 = Event(title='Seminar Deep Dive', start_time=base + timedelta(hours=2), end_time=base + timedelta(hours=4), description='Overlap with e1')
    e3 = Event(title='Short Class', start_time=base + timedelta(hours=3), end_time=base + timedelta(hours=3, minutes=30), description='Edge case partial overlap')
    e4 = Event(title='Touching Event', start_time=base + timedelta(hours=4), end_time=base + timedelta(hours=5), description='Touching boundary with e2 end')

    db.session.add_all([e1, e2, e3, e4])
    db.session.commit()

    # Allocations (with overlaps for conflict view)
    db.session.add_all([
        EventResourceAllocation(event_id=e1.event_id, resource_id=r1.resource_id),
        EventResourceAllocation(event_id=e1.event_id, resource_id=r3.resource_id),
        EventResourceAllocation(event_id=e2.event_id, resource_id=r1.resource_id),  # conflict with e1 on Room A
        EventResourceAllocation(event_id=e2.event_id, resource_id=r4.resource_id),
        EventResourceAllocation(event_id=e3.event_id, resource_id=r3.resource_id),  # partial overlap on projector
        EventResourceAllocation(event_id=e4.event_id, resource_id=r2.resource_id),
    ])
    db.session.commit()

    print('Seeded sample data with overlapping events and allocations.')
