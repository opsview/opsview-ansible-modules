# Opsview Ansible Modules

**Ansible modules for interacting with Opsview Monitor!**

![Opsview Logo](https://raw.githubusercontent.com/opsview/pyopsview/master/opsview.png)

## Requirements

* [ansible](https://github.com/ansible/ansible "ansible") >= 2.0
* [pyopsview](https://github.com/opsview/pyopsview "pyopsview") >= 5.3.3

## Installing 

```bash
# Replace /etc/ansible with wherever your playbooks live

sudo pip install 'pyopsview>=5.3.3'

sudo mkdir /etc/ansible/library/
sudo mkdir /etc/ansible/module_utils/

git clone https://github.com/opsview/opsview-ansible-modules.git

sudo cp -p opsview-ansible-modules/library/*.py /etc/ansible/library
sudo cp -p opsview-ansible-modules/module_utils/*.py /etc/ansible/module_utils
```

## Documentation

All of the documentation is available with `ansible-doc`

## Examples

```yaml
---
- hosts: webservers_eu_west
  connection: local
  vars:
    opsview_username: admin
    opsview_password: initial
    opsview_endpoint: http://opsview.example.com

  handlers:
    - name: Reload Opsview
      opsview_reload:
        username: '{{ opsview_username }}'
        endpoint: '{{ opsview_endpoint }}'
        token: '{{ opsview_login.token }}'
      # Handle failures in case there's already a reload in progress.
      register: reload_status
      ignore_errors: true
      until: reload_status|succeeded
      retries: 3
      delay: 30

  tasks:
    # Speed up operations by logging into Opsview first and using the
    # auth token directly
    - name: Log into Opsview
      opsview_login:
        username: '{{ opsview_username }}'
        password: '{{ opsview_password }}'
        endpoint: '{{ opsview_endpoint }}'
      register: opsview_login
      delegate_to: localhost

    - name: Create the WebServer hostgroup
      opsview_host_group:
        username: '{{ opsview_username }}'
        token: '{{ opsview_login.token }}'
        endpoint: '{{ opsview_endpoint }}'
        name: Web Servers
        parent: Production EU West 1
      notify: Reload Opsview
      delegate_to: localhost
      run_once: true
      register: webserver_host_group

    - debug:
        msg: 'Web Server Host Group ID: {{ webserver_host_group.object_id }}'

    - name: Add WebServer to Opsview
      opsview_host:
        username: '{{ opsview_username }}'
        token: '{{ opsview_login.token }}'
        endpoint: '{{ opsview_endpoint }}'
        name: '{{ ansible_hostname | default(inventory_hostname) }}'
        address: '{{ ansible_default_ipv4.address }}'
        monitored_by: Master Monitoring Server
        host_group: Web Servers
        host_templates:
          - Network - Base
          - OS - Opsview Agent
          - OS - Unix Advanced
        service_checks:
          # Lists can be specified in a simple format:
          - Apache current requests
          # Or in a dictionary format if more fields need to be supplied:
          - name: Zombie Processes
            remove_service_check: true
        notify: Reload Opsview
        delegate_to: localhost
```
      
## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request
