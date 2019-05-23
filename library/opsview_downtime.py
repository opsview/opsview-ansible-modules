#!python
# -*- coding: utf-8 -*-

# (c) 2017, Opsview Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = """
"""

import hashlib
import os.path
import traceback
from datetime import datetime
from datetime import timedelta

from ansible.module_utils import opsview as ov
from ansible.module_utils.basic import to_native
from ansible.module_utils.six import iteritems
from ansible.module_utils.six import string_types

ARG_SPEC = {
    "endpoint": {
        "required": True
    },
    "password": {
        "no_log": True,
    },
    "token": {
        "no_log": True,
    },
    "username": {
        "required": True
    },
    "verify_ssl": {
        "default": True
    },
    "state": {
        "choices": [
            "present",
            "absent",
        ],
        "default": "present",
    },
    "host": {
        "required": True,
    },
    "duration": {
        "default": "1h",
    },
    "comment": {
        "required": False,
    },
}

ARG_KEYS = tuple(ARG_SPEC.keys())


def downtime_ident(host):
    """Return a determinate identifier for matching downtime comments."""
    return "ansible_id={!s}".format(
        hashlib.sha256(host).hexdigest()[0:16]
    )


def downtime_comment(host, comment=None):
    """Return the comment with the ansible identifier appended."""
    ident = downtime_ident(host)
    if comment:
        return "{!s} {!s}".format(comment, ident)
    else:
        return "Created by Ansible. {!s}".format(ident)


def duration_to_timedelta(duration):
    delta = timedelta()

    deltas_by_period = {
        's': timedelta(seconds=1),
        'm': timedelta(minutes=1),
        'h': timedelta(hours=1),
        'd': timedelta(days=1),
        'w': timedelta(weeks=1),
    }

    for token in duration.lower().split():
        # .split() guarantees len(token) > 0
        unit = deltas_by_period[token[-1]]
        count = int(token[:-1])
        delta += unit * count

    return delta


def create_downtime(client, host, duration, comment=None):
    # Ensure that the downtime starts immediately by setting the start time
    # slightly in the past (in case the client's clock is slightly in the
    # future)
    start_time = datetime.utcnow() - timedelta(minutes=1)
    try:
        end_time = start_time + duration_to_timedelta(duration)
    except Exception:
        raise ValueError("Invalid duration: {!r}".format(duration))

    comment = downtime_comment(host, comment)

    body = {
        'comment': comment,
        'starttime': "{!s}".format(start_time),
        'endtime': "{!s}".format(end_time),
    }

    params = {
        'hst.hostname': host
    }

    response = client.post('downtime', params=params, data=body)
    return response


def find_downtime(client, host, comment=None):
    ident = downtime_ident(host)

    params = {
        'object_count_only': True,
        'comment': '%{!s}'.format(ident),
    }

    # XXX The response should be paged but, as this is called many times, it's
    #     not strictly necessary (it's called after each 'delete' call)
    response = client.get('downtime', params=params)

    with open('/tmp/response', 'w') as fh:
        print(response, file=fh)

    matches = []
    for obj in response['list']:
        # comment needs to contain the ansible identifier
        if not obj['comment'].endswith(ident):
            continue

        matches.append(obj)

    return matches


def delete_downtime(client, host, comment=None):
    changed = False

    while True:
        matches = find_downtime(client, host, comment)
        if not matches:
            return changed

        changed = True

        for match in matches:
            params = {
                'only_objects_set': True,
                'start_time': match['start_time'],
                'comment': match['comment'],
            }
            client.delete('downtime', params=params)

    return changed


def module_main(module):
    verify = module.params['verify_ssl']

    if not os.path.exists(verify):
        verify = module.boolean(verify)

    opsview_client = ov.new_opsview_client(
        username=module.params['username'],
        password=module.params['password'],
        endpoint=module.params['endpoint'],
        token=module.params['token'],
        verify=verify,
    )

    if module.params['state'] == 'present':
        create_downtime(
            opsview_client,
            module.params['host'],
            module.params['duration'],
            module.params['comment'],
        )
        return {'changed': True}
    elif module.params['state'] == 'absent':
        changed = delete_downtime(
            opsview_client,
            module.params['host'],
            module.params['comment'],
        )
        return {'changed': changed}
    else:
        raise ValueError("Unknown state: {!r}".format(module.params['state']))


def main():
    module = ov.new_module(ARG_SPEC, always_include=ARG_KEYS)
    # Handle exception importing 'pyopsview'
    if ov.PYOV_IMPORT_EXC is not None:
        module.fail_json(msg=ov.PYOV_IMPORT_EXC[0],
                         exception=ov.PYOV_IMPORT_EXC[1])

    try:
        summary = module_main(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(**summary)


if __name__ == '__main__':
    main()
