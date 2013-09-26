import os.path
from setuptools import setup, find_packages

cwd = os.path.abspath(os.path.dirname(__file__))

setup(
    name='poncho',
    description='poncho: smart actions for full clouds',
    version='0.1.0',
    author='Scott Devoid',
    author_email='devoid@anl.gov',
    url='https://github.com/magellancloud/poncho',
    license='LICENSE.txt',
    long_description=open(cwd + '/README.txt').read(),
    install_requires=[
        "python-novaclient >= 2.0.0",
        "anyjson >= 0.3.3",
        "alembic >= 0.5",
        "oslo.config >= 1.1.1",
        "SQLAlchemy>=0.7,<=0.7.99",
        "importlib",
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts' : [
              'poncho = poncho.cmd.client:main',
              'poncho-service = poncho.cmd.service:main',
              'poncho-daemon = poncho.cmd.service_worker:main',
        ],
    },
)

