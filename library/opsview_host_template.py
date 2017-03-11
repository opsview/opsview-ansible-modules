#!/usr/bin/env python

from ansible.module_utils.basic import *
from pyopsview.ansible.module_utils.opsview import OpsviewAnsibleModuleAdvanced

if __name__ == '__main__':
    module = OpsviewAnsibleModuleAdvanced('hosttemplates')

    try:
        module()
    except Exception as ex:
        module.fail(str(ex))
    else:
        module.exit()
