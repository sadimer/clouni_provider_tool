#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: equals
short_description: implementation of equals artifact
author:
    - Roman Stolyarov (Sadimer)
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    HAS_LIB = True
except:
    HAS_LIB = False

from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = dict(
        input_facts=dict(type='list', required=True),
        input_args=dict(type='list', required=True),
    )
    ansible_module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    input_facts = ansible_module.params['input_facts']
    if len(ansible_module.params['input_args']) != 2:
        ansible_module.fail_json(msg="Bad input args, should use 0 arg for match parameter and 1 arg for match value")
    match_param = ansible_module.params['input_args'][0]
    match_val = ansible_module.params['input_args'][1]
    results = []
    for elem in input_facts:
        if elem.get(match_param) == match_val:
            results.append(elem)
    if len(results) == 0:
        ansible_module.fail_json(msg="There are no matchable objects")
    elif len(results) > 1:
        ansible_module.warn(warning="WARNING: there are more than one matchable objects")
        ansible_module.exit_json(matched_object=results[-1])
    else:
        ansible_module.exit_json(matched_object=results[-1])


if __name__ == '__main__':
    main()
