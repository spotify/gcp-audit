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

import re
import operator


def filterjson(event, filter, matchtype, listcondition="or"):
    match = True

    if isinstance(filter, dict):
        for k, v in filter.iteritems():
            if k in event:
                if isinstance(v, dict):
                    match = filterjson(event[k], v, matchtype, listcondition)
                elif isinstance(v, list) and isinstance(event[k], list):
                    match = filterjson(event[k], v, matchtype, listcondition)
                else:
                    # Match filter string against object array
                    if isinstance(event[k], list):
                        for e in event[k]:
                            match = filterjson(e, v, matchtype)
                            if match:
                                break
                    # Match filter string against object string, int, bool
                    else:
                        match = matchstr(event[k], v, matchtype)
            else:
                # For count checks, handle a missing key
                # as if the key were an empty list
                if matchtype == "count":
                    match = matchstr([], v, matchtype)
                else:
                    match = False

            if not match:
                break
    elif isinstance(filter, list) and isinstance(event, list):
        for f in filter:
            for e in event:
                match = filterjson(e, f, matchtype, listcondition)
                if ((listcondition == 'or' and match) or
                   (listcondition == 'and' and not match)):
                    break
    elif isinstance(filter, list):
        for v in filter:
            match = filterjson(event, v, matchtype, listcondition)
            if ((listcondition == 'or' and match) or
               (listcondition == 'and' and not match)):
                break
    elif isinstance(filter, basestring):
        match = matchstr(event, filter, matchtype)
    else:
        raise "ERROR, unknown object encountered"
    return match


def matchstr(estr, fstr, matchtype):
    if matchtype == 'count' or matchtype == 'numeric':
        ops = {"lt": operator.lt,
               "gt": operator.gt,
               "eq": operator.eq}

        op, val = fstr.split()
        val = int(val)

    if matchtype == 'exact':
        match = (fstr == estr)
    elif matchtype == 'partial':
        match = estr.find(fstr)
    elif matchtype == 'regex':
        match = (re.search(fstr, estr) is not None)
    elif matchtype == 'numeric':
        match = isinstance(estr, (int, long) and ops[op](estr, val))
    elif matchtype == 'count':
        # All other objects than lists are single objects
        if isinstance(estr, list):
            objlen = len(estr)
        else:
            objlen = 1

        match = ops[op](objlen, val)
    else:
        raise "ERROR: unknown mode"

    return match
