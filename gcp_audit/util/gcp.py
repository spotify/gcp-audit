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

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


def create_service(service, version='v1'):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build(service, version, credentials=credentials)

    return service


def get_firewalls(project):
    service = create_service('compute')
    req = service.firewalls().list(project=project)

    try:
        res = req.execute()['items']
    except:
        res = []

    return res


def get_buckets(project):
    service = create_service('storage')
    req = service.buckets().list(project=project)
    try:
        res = req.execute()['items']
    except:
        res = []

    return res


def get_default_acls(project):
    res = []

    for bucket in get_buckets(project):
        res.extend(get_default_access_controls(project, bucket["name"]))

    return res


def get_default_access_controls(project, bucket):
    service = create_service('storage')
    req = service.defaultObjectAccessControls().list(bucket=bucket)
    try:
        res = req.execute()['items']
    except:
        res = []

    return res


def get_acls_for_bucket(project, bucket):
    service = create_service('storage')
    req = service.bucketAccessControls().list(bucket=bucket)

    try:
        res = req.execute()['items']
    except:
        res = []

    return res


def get_acls_for_buckets(project):
    res = []

    for bucket in get_buckets(project):
        res += get_acls_for_bucket(project, bucket['name'])

    return res


def get_cloudsql_instances(project):
    service = create_service(service='sqladmin', version='v1beta4')
    req = service.instances().list(project=project)

    try:
        res = req.execute()['items']
    except:
        res = []

    return res


def get_projects_for_organization(organization_id):
    projects = []
    page_token = None

    while True:
        resp = create_service('cloudresourcemanager', 'v1beta1').projects() \
            .list(filter='parent.id:%s' % organization_id,
                  pageSize=250,
                  pageToken=page_token).execute()

        projects += [x['projectId'] for x in resp['projects']]

        page_token = resp.get('nextPageToken', None)
        if not page_token:
            break

    return projects


def get_all_organizations():
    """Get all organizations that the credentials have access to."""
    resp = create_service('cloudresourcemanager', 'v1beta1') \
        .organizations().list().execute()

    return [x['organizationId'] for x in resp['organizations']]


def get_all_projects():
    """Get all organizations that the credentials have access to."""
    projects = []

    for org in get_all_organizations():
        projects += get_projects_for_organization(org)

    return projects
