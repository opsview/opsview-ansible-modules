# Opsview Ansible Modules

**Ansible modules for interacting with Opsview Monitor!**

![Opsview Logo](https://raw.githubusercontent.com/jpgxs/pyopsview/master/opsview.png)

## Requirements

* [ansible](https://github.com/ansible/ansible "ansible") >= 2.0
* [pyopsview](https://github.com/jpgxs/pyopsview "pyopsview") >= 5.3.2

## Installing 

```bash
# Replace /etc/ansible with wherever your playbooks live

sudo pip install 'pyopsview>=5.3.2'

sudo mkdir /etc/ansible/library

git clone https://github.com/jpgxs/ansible-modules-opsview.git

sudo cp -p ansible-modules-opsview/library/*.py /etc/ansible/library
```

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
        name: '{{ ansible_hostname }}'
        address: '{{ ansible_default_ipv4 }}'
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
