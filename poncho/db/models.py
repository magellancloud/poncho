# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
SQLAlchemy models for poncho.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer
from sqlalchemy import String, schema, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, object_mapper
from datetime import datetime

BASE = declarative_base()

host_association_table = Table(
    'service_events_to_hosts', BASE.metadata,
    Column('service_event_id', Integer, ForeignKey('service_events.id')),
    Column('host_id', Integer, ForeignKey('hosts.id')),
)


class ServiceEvent(BASE):
    """Represents a single service event."""
    __tablename__ = 'service_events'
    __table_args__ = ()
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=False)
    workflow = Column(String, nullable=False)
    begin_passive_drain_at = Column(DateTime, nullable=False)
    begin_active_drain_at = Column(DateTime, nullable=False)
    state = Column(String, default='initialized')
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    hosts = relationship("Host", secondary=host_association_table,
                         backref="service_events")

     

class Host(BASE):
    """Represents a single host on the system."""
    __tablename__ = 'hosts'
    __table_args__ = ()
    # Note that all status is gathered from the nova APIs.
    # This just maintains relationships with the service event table; when
    # a service event is completed, the host should only be reactivated if
    # there are no additional service events 
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    instances = relationship("Instance")
        

class Instance(BASE):
    """Represents the status of instance notifications and operations."""
    __tablename__ = 'instance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String)
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime)
    host_id = Column(Integer, ForeignKey('hosts.id'))
