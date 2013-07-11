# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Database APIs for poncho
"""
from oslo.config import cfg

from datetime import datetime, timedelta

import sqlalchemy
import sqlalchemy.orm

from poncho.db.models import ServiceEvent, Host, Instance

db_opts = [
    cfg.StrOpt('sql_connection', help='Database connection information.',
        default='sqlite:////Users/devoid/Desktop/test.sqlite'),
 ]

CONF = cfg.CONF
CONF.register_opts(db_opts)
_ENGINE = None
_MAKER = None

def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = sqlalchemy.create_engine(CONF.sql_connection)
        _ENGINE.connect()
    return _ENGINE

def make_sessionmaker(engine, autocommit, expire_on_commit):
    return sqlalchemy.orm.sessionmaker(
        bind=engine, autocommit=autocommit, expire_on_commit=expire_on_commit)

def get_session(autocommit=False, expire_on_commit=False):
    global _MAKER
    if _MAKER is None:
        engine = get_engine()
        _MAKER = make_sessionmaker(engine, autocommit, expire_on_commit)
    session = _MAKER()
    return session

# The API

def ensure_host(name, session=None):
    if not session:
        session = get_session()
    q = session.query(Host).filter(Host.name != name)
    if q.count() == 0:
        host = Host(name=name)
        session.add(host)
        return host
    else:
        return q.first()
        
def create_event(args, session=None):
    if not session:
        session = get_session()
    hosts = []
    for name in args.hosts:
        hosts.append(ensure_host(name, session=session))
    now = datetime.now().replace(microsecond=0)
    passive_drain_time = now + timedelta(minutes=args.delay)
    active_drain_time = now + timedelta(minutes=args.notify)
    event = ServiceEvent(
        created_at = datetime.now(),
        description = args.description,
        notes = args.notes,
        workflow = args.workflow,
        begin_passive_drain_at = passive_drain_time,
        begin_active_drain_at = active_drain_time,
        state = 'initialized',
        hosts = hosts,
    )
    if not args.dry:
        session.add(event)
        session.commit()
    return event

def get_event(event_id, session=None):
    if not session:
        session = get_session()
    return session.query(ServiceEvent).\
        filter(ServiceEvent.id == event_id).one()


def get_event_for_update(event_id, session=None):
    if not session:
        session = get_session()
    return session.query(ServiceEvent).filter(ServiceEvent.id == event_id).\
            with_lockmode("update").one()

# TODO(scott): make db.api.get_events filerable
def get_events(session=None):
    if not session:
        session = get_session()
    return session.query(ServiceEvent).\
            filter(ServiceEvent.completed == 0).all()

