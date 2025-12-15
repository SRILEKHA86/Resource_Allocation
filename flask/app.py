from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import and_, or_
from forms import EventForm, ResourceForm, AllocationForm, ReportForm
from models import db, Event, Resource, EventResourceAllocation
from utils import intervals_overlap, clamp_interval, hours_between


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'  # replace in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app: Flask):
    @app.route('/')
    def index():
        return render_template('base.html')

    # Resources CRUD
    @app.route('/resources')
    def resources_list():
        resources = Resource.query.order_by(Resource.resource_name).all()
        return render_template('resources/index.html', resources=resources)

    @app.route('/resources/new', methods=['GET', 'POST'])
    def resources_new():
        form = ResourceForm()
        if form.validate_on_submit():
            r = Resource(resource_name=form.resource_name.data.strip(), resource_type=form.resource_type.data.strip())
            db.session.add(r)
            db.session.commit()
            flash('Resource created', 'success')
            return redirect(url_for('resources_list'))
        return render_template('resources/form.html', form=form, action='Create')

    @app.route('/resources/<int:resource_id>/edit', methods=['GET', 'POST'])
    def resources_edit(resource_id):
        r = Resource.query.get_or_404(resource_id)
        form = ResourceForm(obj=r)
        if form.validate_on_submit():
            r.resource_name = form.resource_name.data.strip()
            r.resource_type = form.resource_type.data.strip()
            db.session.commit()
            flash('Resource updated', 'success')
            return redirect(url_for('resources_list'))
        return render_template('resources/form.html', form=form, action='Update')

    # Events CRUD
    @app.route('/events')
    def events_list():
        events = Event.query.order_by(Event.start_time).all()
        return render_template('events/index.html', events=events)

    @app.route('/events/new', methods=['GET', 'POST'])
    def events_new():
        form = EventForm()
        form.resources.choices = [(r.resource_id, f"{r.resource_name} ({r.resource_type})") for r in Resource.query.order_by(Resource.resource_name)]
        if form.validate_on_submit():
            event = Event(
                title=form.title.data.strip(),
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                description=form.description.data.strip() if form.description.data else ''
            )
            db.session.add(event)
            db.session.flush()

            selected_ids = form.resources.data or []
            # Conflict check for each resource
            conflicts = []
            for rid in selected_ids:
                if has_conflict(rid, event.start_time, event.end_time, exclude_event_id=None):
                    res = Resource.query.get(rid)
                    conflicts.append(f"{res.resource_name} ({res.resource_type})")
            if conflicts:
                db.session.rollback()
                flash(f"Conflict: resources already booked -> {', '.join(conflicts)}", 'danger')
                return render_template('events/form.html', form=form, action='Create')

            # Save allocations
            for rid in selected_ids:
                db.session.add(EventResourceAllocation(event_id=event.event_id, resource_id=rid))

            db.session.commit()
            flash('Event created', 'success')
            return redirect(url_for('events_list'))
        return render_template('events/form.html', form=form, action='Create')

    @app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
    def events_edit(event_id):
        event = Event.query.get_or_404(event_id)
        form = EventForm(obj=event)
        form.resources.choices = [(r.resource_id, f"{r.resource_name} ({r.resource_type})") for r in Resource.query.order_by(Resource.resource_name)]
        if request.method == 'GET':
            form.resources.data = [a.resource_id for a in event.allocations]
        if form.validate_on_submit():
            # Update fields
            event.title = form.title.data.strip()
            event.start_time = form.start_time.data
            event.end_time = form.end_time.data
            event.description = form.description.data.strip() if form.description.data else ''

            selected_ids = set(form.resources.data or [])
            current_ids = set(a.resource_id for a in event.allocations)

            # Conflict check for added resources
            added = selected_ids - current_ids
            conflicts = []
            for rid in selected_ids:  # check all selected in case time changed
                if has_conflict(rid, event.start_time, event.end_time, exclude_event_id=event.event_id):
                    res = Resource.query.get(rid)
                    conflicts.append(f"{res.resource_name} ({res.resource_type})")
            if conflicts:
                db.session.rollback()
                flash(f"Conflict: resources already booked -> {', '.join(conflicts)}", 'danger')
                return render_template('events/form.html', form=form, action='Update')

            # Apply allocation changes
            for a in list(event.allocations):
                if a.resource_id not in selected_ids:
                    db.session.delete(a)
            for rid in added:
                db.session.add(EventResourceAllocation(event_id=event.event_id, resource_id=rid))

            db.session.commit()
            flash('Event updated', 'success')
            return redirect(url_for('events_list'))
        return render_template('events/form.html', form=form, action='Update')

    # Allocations page (alternative to selecting in Event form)
    @app.route('/allocations', methods=['GET', 'POST'])
    def allocations_index():
        form = AllocationForm()
        form.event_id.choices = [(e.event_id, f"{e.title} ({e.start_time:%Y-%m-%d %H:%M} → {e.end_time:%H:%M})") for e in Event.query.order_by(Event.start_time)]
        form.resources.choices = [(r.resource_id, f"{r.resource_name} ({r.resource_type})") for r in Resource.query.order_by(Resource.resource_name)]

        if form.validate_on_submit():
            event = Event.query.get(form.event_id.data)
            selected_ids = set(form.resources.data or [])
            # Check conflicts for all selected
            conflicts = []
            for rid in selected_ids:
                if has_conflict(rid, event.start_time, event.end_time, exclude_event_id=event.event_id):
                    res = Resource.query.get(rid)
                    conflicts.append(f"{res.resource_name} ({res.resource_type})")
            if conflicts:
                flash(f"Conflict: resources already booked -> {', '.join(conflicts)}", 'danger')
                return render_template('allocations/index.html', form=form)

            # Apply allocations (merge behavior)
            current_ids = set(a.resource_id for a in event.allocations)
            to_add = selected_ids - current_ids
            for rid in to_add:
                db.session.add(EventResourceAllocation(event_id=event.event_id, resource_id=rid))
            db.session.commit()
            flash('Resources allocated to event', 'success')
            return redirect(url_for('events_list'))

        return render_template('allocations/index.html', form=form)

    # Conflicts view
    @app.route('/conflicts')
    def conflicts_view():
        conflicts = []
        resources = Resource.query.all()
        for r in resources:
            # All events for this resource
            evts = [a.event for a in r.allocations]
            evts.sort(key=lambda e: e.start_time)
            for i in range(len(evts)):
                for j in range(i + 1, len(evts)):
                    e1, e2 = evts[i], evts[j]
                    if intervals_overlap(e1.start_time, e1.end_time, e2.start_time, e2.end_time):
                        conflicts.append((r, e1, e2))
        return render_template('conflicts/index.html', conflicts=conflicts)

    # Utilisation report
    @app.route('/report', methods=['GET', 'POST'])
    def report_view():
        form = ReportForm()
        results = None
        if form.validate_on_submit():
            start = form.range_start.data
            end = form.range_end.data
            if start >= end:
                flash('Invalid range: Start must be before end.', 'danger')
            else:
                results = []
                now = datetime.now()
                for r in Resource.query.order_by(Resource.resource_name):
                    total_seconds = 0
                    upcoming = []
                    for a in r.allocations:
                        e = a.event
                        # Overlap with selected range
                        over = clamp_interval(e.start_time, e.end_time, start, end)
                        if over:
                            total_seconds += hours_between(over[0], over[1]) * 3600
                        if e.start_time >= now and e.start_time <= end:
                            upcoming.append(e)
                    results.append({
                        'resource': r,
                        'total_hours': round(total_seconds / 3600, 2),
                        'upcoming': sorted(upcoming, key=lambda x: x.start_time)
                    })
        return render_template('report/index.html', form=form, results=results)

    def has_conflict(resource_id: int, start_time: datetime, end_time: datetime, exclude_event_id=None) -> bool:
        q = (
            db.session.query(Event)
            .join(EventResourceAllocation, Event.event_id == EventResourceAllocation.event_id)
            .filter(EventResourceAllocation.resource_id == resource_id)
        )
        if exclude_event_id:
            q = q.filter(Event.event_id != exclude_event_id)
        # Overlap condition: s1 < e2 and s2 < e1
        q = q.filter(and_(Event.start_time < end_time, start_time < Event.end_time))
        return db.session.query(q.exists()).scalar()


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
