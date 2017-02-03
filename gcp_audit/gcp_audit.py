#!/usr/bin/env python

# Copyright (c) 2016-2017 Spotify AB.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import atexit
import datetime
import googleapiclient
import json
import os
import signal
import sys
import util.gcp as gcp
import yaml

from argparse import ArgumentParser
from termcolor import colored
from util.filter import filterjson


env_credentials = ''

checks = {
    'buckets': {
        'func': gcp.get_acls_for_buckets,
        'descfield': 'bucket'
    },
    'bucket_objects': {
        'func': gcp.get_default_acls,
        'descfield': 'entity'
    },
    'cloudsql': {
        'func': gcp.get_cloudsql_instances,
        'descfield': 'name'
    },
    'firewalls': {
        'func': gcp.get_firewalls,
        'descfield': 'name'
    }
}


def loadrules(ruletype):
    rules = []
    path = os.path.join(os.path.dirname(__file__), "rules/%s" % ruletype)
    for file in os.listdir(path):
        with open("%s/%s" % (path, file)) as rulefile:
            if file.endswith(".json"):
                rule = json.load(rulefile)
            elif file.endswith(".yaml"):
                rule = yaml.safe_load(rulefile)
            else:
                raise "Unknown rule format"
            rules.append(rule)
    return rules


def apply_rules(ruletype, gcpobjects, descfield, outfile, project):
    rules = loadrules(ruletype)
    for obj in gcpobjects:
        for rule in rules:
            if 'filtercondition' in rule:
                res = apply_rule_filters(obj, rule['filters'],
                                         rule['filtercondition'])
            else:
                res = apply_rule_filters(obj, rule['filters'])

            if res:
                print colored('MATCH:', 'red'), \
                    "object '%s' matches rule '%s'" \
                    % (obj[descfield], rule['name'])

                with open(outfile, 'a') as f:
                    f.write(datetime.datetime.now().ctime()
                            + ": Project: " + project
                            + " | Object: " + obj[descfield]
                            + " | Matches rule: " + rule['name']
                            + "\n" + json.dumps(obj) + "\n\n")


def apply_rule_filters(obj, filters, filtercondition='and'):
    res = True

    for f in filters:
        if 'listcondition' in f:
            res = filterjson(obj,
                             f['filter'],
                             f['matchtype'],
                             f['listcondition'])
        else:
            res = filterjson(obj, f['filter'], f['matchtype'])

        if ((filtercondition == 'or' and res) or
           (filtercondition == 'and' and not res)):
            break

    return res


def handle_signal(signal, frame):
    print "SIGINT received. Exiting."
    sys.exit(0)


def parse_options():
    def comma_split(str):
        return str.split(',')

    parser = ArgumentParser(description='A tool for auditing security \
                                         properties of GCP projects.',
                            epilog='gcp-audit needs a valid key for an account \
                                    with audit capabilities for the projects \
                                    in scope in order to work. This needs \
                                    to be set either via the \
                                    GOOGLE_APPLICATION_CREDENTIALS \
                                    environment variable, \
                                    or via the -k parameter.')
    parser.add_argument('-c', '--checks',
                        help='comma separated list of types of checks to run')
    parser.add_argument('-k', '--keyfile',
                        help="keyfile to use for GCP credentials")
    parser.add_argument('-o', '--output',
                        help='file to output results to',
                        default='results.json')
    parser.add_argument('-p', '--projects',
                        help='comma separated list of GCP projects to audit',
                        type=comma_split)

    options = parser.parse_args()

    return options


def restore_env_credentials():
    if env_credentials:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = env_credentials
    else:
        os.unsetenv('GOOGLE_APPLICATION_CREDENTIALS')


def main():
    global checks
    global env_credentials

    options = parse_options()

    signal.signal(signal.SIGINT, handle_signal)

    if options.checks:
        checks = dict((k, v) for k, v in checks.iteritems()
                      if k in options.checks.split(','))

    if options.keyfile:
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            env_credentials = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        atexit.register(restore_env_credentials)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = options.keyfile

    if options.projects:
        projects = options.projects
    else:
        projects = gcp.get_all_projects()

    for project in projects:
        print colored('Project:', 'blue'), project
        for name, check in checks.iteritems():
            try:
                res = check['func'](project)
                apply_rules(name, res, check['descfield'],
                            options.output, project)
            except googleapiclient.errors.HttpError:
                print colored('ERROR:', 'red'), "Permission denied?"

    print colored('DONE', 'green'), \
        ' - results (if any) have been written to %s' % options.output


if __name__ == "__main__":
    main()
