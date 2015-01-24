#!/usr/bin/env python
'''
Application manager.  Responsible for starting the service,
performing db migrations, testing.

'''
import os
basedir = os.path.abspath(os.path.dirname(__file__))
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True,include=basedir + '/app/*')
    COV.start()
from ooiservices.app import create_app, db
from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import Migrate, MigrateCommand


app = create_app('LOCAL_DEVELOPMENT')
manager = Manager(app)
migrate = Migrate(app,db)

def make_shell_context():
    from ooiservices.app.models import User, UserScope, UserScopeLink, Array
    from ooiservices.app.models import PlatformDeployment, InstrumentDeployment, Stream, StreamParameter, Watch
    from ooiservices.app.models import OperatorEvent
    from ooiservices.app.models import Platformname, Instrumentname


    ctx = {"app": app,
           "db": db,
           "User": User,
           "UserScope": UserScope,
           "UserScopeLink": UserScopeLink,
           "Array": Array,
           "PlatformDeployment": PlatformDeployment,
           "InstrumentDeployment": InstrumentDeployment,
           "Stream": Stream,
           "Watch": Watch,
           "OperatorEvent": OperatorEvent,
           "StreamParameter": StreamParameter,
           "Platformname": Platformname,
           "Instrumentname": Instrumentname}
    return ctx

@manager.command
def runserver():
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=True)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def test(coverage=False):
    import sys
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    retval = unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        COV.erase()
    if retval.errors:
        sys.exit(1)
    if retval.failures:
        sys.exit(1)

@manager.option('-p', '--password', required=True)
def deploy(password):
    from flask.ext.migrate import upgrade
    from ooiservices.app.models import User, UserScope, UserScopeLink, Array
    from ooiservices.app.models import PlatformDeployment, InstrumentDeployment, Stream, StreamParameterLink
    #Create the local database
    os.system("psql -c 'create database ooiuidev;' -U postgres")
    os.system("psql -c 'create schema ooiui;' ooiuidev")
    os.system("psql -c 'create extension postgis;' ooiuidev")
    #Create the local test database
    os.system("psql -c 'create database ooiuitest;' -U postgres")
    os.system("psql -c 'create schema ooiui;' ooiuitest")
    os.system("psql -c 'create extension postgis;' ooiuitest")
    db.create_all()
    # migrate database to latest revision
    #upgrade()
    User.insert_user(password)

@manager.command
def destroy():
    db_check = str(db.engine)
    if (db_check == 'Engine(postgres://postgres@localhost/ooiuidev)'):
        os.system("psql -c 'drop database ooiuidev;'")
        os.system("psql -c 'drop database ooiuitest;'")
    else:
        print 'Must be working on LOCAL_DEVELOPMENT to destroy db'

if __name__ == '__main__':
    manager.run()
