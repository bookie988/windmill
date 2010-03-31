#   Copyright (c) 2007 Open Source Applications Foundation
#   Copyright (c) 2008-2009 Mikeal Rogers <mikeal.rogers@gmail.com>
#   Copyright (c) 2009 Domen Kozar <domen@dev.si>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import sys
import windmill
from windmill import server, tools
from windmill.dep import json
import tempfile

if not sys.version.startswith('2.4'):
    from urlparse import urlparse
else:
    # python 2.4
    from tools.urlparse_25 import urlparse
    

def get_save_url(suite_name, extension):
    url = urlparse(windmill.settings['TEST_URL'])
    return url.scheme+'://'+url.netloc+'/windmill-saves/'+suite_name+'.'+extension

def create_saves_path():
    directory = tempfile.mkdtemp(suffix='.windmill-saves')
    # Mount the fileserver application for tests
    from webenv.applications.file_server import FileServerApplication
    application = FileServerApplication(os.path.dirname(__file__))
    server.add_namespace('windmill-unittests', application)
    windmill.settings['SAVES_PATH'] = directory
    windmill.teardown_directories.append(directory)

def test_object_transform_to_python(test):
    """Transform test object in to controller call in python."""
    params = ', '.join([key+'='+repr(value) for key, value in test['params'].items()])    
    return 'client.%s(%s)' % (test['method'], params)
    
def build_python_test_file(tests, suite_name=None):
    """Build the test file for python"""
    ts = '# Generated by the windmill services transformer\n'
    ts += 'from windmill.authoring import WindmillTestClient\n\n'
    if suite_name:
        ts += 'def test_'+suite_name.replace('test_', '', 1)+'():\n'
    else:
        ts += 'def test():\n'
    ts += '    client = WindmillTestClient(__name__)\n\n    '
    ts += '\n    '.join([test_object_transform_to_python(test) for test in tests])
    return ts
    
def create_python_test_file(suite_name, tests, location=None):
    """Transform and create and build the python test file"""
    if location is None: 
        location = os.path.join(windmill.settings['SAVES_PATH'], suite_name+'.py')
    f = open(location, 'w')
    f.write(build_python_test_file(tests, suite_name.split('.')[0]))
    f.flush()
    f.close()
    return get_save_url(suite_name, 'py')

def create_json_test_file(suite_name, tests, location=None):
    """Transform and create a json test file."""
    if location is None: 
        location = os.path.join(windmill.settings['SAVES_PATH'], suite_name+'.json')
    f = open(location, 'w')
    for test in tests:
        # Strip keys that aren't part of the api
        test.pop('suite_name', None) ; test.pop('version', None)
        f.write(json.dumps(test))
        f.write('\n')
    f.flush()
    f.close()
    return get_save_url(suite_name, 'json')

def test_object_transform_to_javascript(test):
    """Transform test object in to controller call in javascript."""
    test = dict([(k, v,) for k, v in test.items() if k == 'method' or k == 'params'])
    return json.dumps(test)

def build_javascript_test_file(tests, suite_name=None):
    """Build the test file for javascript"""
    ts = '// Generated by the windmill services transformer\n'
    if suite_name:
        ts += 'var test_'+suite_name.replace('test_', '', 1).split('.')[0]+' = new function() {\n'
    else:
        ts += 'var test_one = new function() {\n'
    ts += '    this.test_actions = [\n'
    ts += ',\n'.join([test_object_transform_to_javascript(test) for test in tests])
    ts += '\n    ];\n'
    ts += '}\n'
    return ts

def create_javascript_test_file(suite_name, tests, location=None):
    """Transform and create and build the javascript test file"""
    if location is None: 
        location = os.path.join(windmill.settings['SAVES_PATH'], suite_name+'.js')
    f = open(location, 'w')
    f.write(build_javascript_test_file(tests, suite_name))
    f.flush()
    f.close()
    return get_save_url(suite_name, 'js')
    
registry = {'python':create_python_test_file, 'json':create_json_test_file, 'javascript': create_javascript_test_file}

