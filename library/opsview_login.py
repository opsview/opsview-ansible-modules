#!/usr/bin/env python

from ansible.module_utils.basic import *
from pyopsview.ansible.module_utils.opsview import OpsviewAnsibleModuleBasic


class OpsviewLoginModule(OpsviewAnsibleModuleBasic):

    argument_spec = {
        'username': {'required': True, 'type': 'str'},
        'password': {'required': True, 'type': 'str'},
        'endpoint': {'required': True, 'type': 'str'},
    }

    def __call__(self):
        self.make_client()
        self.changed = True
        self.status['token'] = self.client.token
        self.status['opsview_version'] = self.client.version


if __name__ == '__main__':
    module = OpsviewLoginModule()

    try:
        module()
    except Exception as ex:
        module.fail(str(ex))
    else:
        module.exit()
