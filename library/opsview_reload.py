#!/usr/bin/env python

import time
from ansible.module_utils import six
from ansible.module_utils.basic import *
from pyopsview.ansible.module_utils.opsview import OpsviewAnsibleModuleBasic


class OpsviewReloadModule(OpsviewAnsibleModuleBasic):

    argument_spec = {
        'username': {'required': True, 'type': 'str'},
        'token': {'required': True, 'type': 'str'},
        'endpoint': {'required': True, 'type': 'str'},
        'force': {'default': False, 'type': 'bool'},
    }

    reload_status_codes = {
        0: 'Server running with no warnings',
        1: 'Server reloading',
        2: 'Server not running',
        3: 'Configuration error or critical error',
        4: 'Warnings exist',
    }

    def reload_status(self):
        status = self.client.reload_status()

        # Attempt to marshall numeric fields into integers
        for key, value in six.iteritems(status):
            try:
                status[key] = int(value)
            except Exception:
                pass

        return status

    def reload(self):
        status = self.reload_status()
        reload_status = status['server_status']
        config_status = status['configuration_status']

        # Fail if it's pretty much impossible to reload
        if reload_status in [1, 2]:
            self.fail_json(self.reload_status_codes[reload_status])

        # Don't reload unless a reload is pending or `force` was specified
        if config_status.lower() == 'pending' or self.params['force']:
            self.changed = True
            self.client.reload(async=True)
            self.wait_reload()

        status = self.reload_status()
        reload_status = status['server_status']

        if reload_status == 4:
            # Add warnings
            for message in status['messages']:
                self.warn('Opsview: ' + message)

        elif reload_status in [2, 3]:
            self.fail('Failed to reload: %s' %
                      reload_status_codes[reload_status])

        self.status.update(status)

    def wait_reload(self):
        while True:
            status = self.reload_status()
            reload_status = status['server_status']

            if reload_status != 1:
                break

            # This needs to be different from the TCP keepalive seconds
            # otherwise weird stuff will happen
            time.sleep(7)

    def __call__(self):
        self.make_client()
        self.reload()


if __name__ == '__main__':
    module = OpsviewReloadModule()

    try:
        module()
    except Exception as ex:
        module.fail(str(ex))
    else:
        module.exit()
