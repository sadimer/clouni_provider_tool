from shutil import copyfile

from provider_tool.common.translator_to_configuration_dsl import translate as common_translate
import os
import yaml
import copy
import difflib

from provider_tool.common.utils import deep_update_dict
from provider_tool.common.tosca_reserved_keys import *

TEST = 'test'

class BaseProvider:
    TESTING_TEMPLATE_FILENAME_TO_JOIN = ['testing', 'examples', 'testing-example.yaml']
    NODE_NAME = 'tosca_server_example'
    DEFAULT_TEMPLATE = {
        TOSCA_DEFINITIONS_VERSION: "tosca_simple_yaml_1_0",
        TOPOLOGY_TEMPLATE: {
            NODE_TEMPLATES: {
                NODE_NAME: {
                    TYPE: "tosca.nodes.Compute"
                }
            }
        }
    }

    def template_filename(self):
        r = None
        for i in self.TESTING_TEMPLATE_FILENAME_TO_JOIN:
            if r == None:
                r = i
            else:
                r = os.path.join(r, i)
        return r

    def read_template(self, filename=None):
        if not filename:
            filename = self.template_filename()
        with open(filename, 'r') as f:
            return f.read()

    def write_template(self, template, filename=None):
        if not filename:
            filename = self.template_filename()
        with open(filename, 'w') as f:
            f.write(template)

    def delete_template(self, filename=None):
        if not filename:
            filename = self.template_filename()
        if os.path.exists(filename):
            os.remove(filename)

    def parse_yaml(self, content):
        r = yaml.load(content, Loader=yaml.Loader)
        return r

    def parse_all_yaml(self, content):
        r = yaml.full_load_all(content)
        return r

    def prepare_yaml(self, content):
        r = yaml.dump(content)
        return r

    def test_provider(self):
        assert hasattr(self, 'PROVIDER') is not None
        assert self.PROVIDER in PROVIDERS

    def get_default_node(self, template):
        self.assertIsNotNone(template.get(TOPOLOGY_TEMPLATE))
        node_templates = template.get(TOPOLOGY_TEMPLATE).get(NODE_TEMPLATES)
        self.assertIsNotNone(node_templates)
        node = node_templates.get(self.NODE_NAME + self.COMPUTE)
        self.assertIsNotNone(node)
        return node

    def get_node(self, template, search_node):
        self.assertIsNotNone(template.get(TOPOLOGY_TEMPLATE))
        node_templates = template.get(TOPOLOGY_TEMPLATE).get(NODE_TEMPLATES)
        self.assertIsNotNone(node_templates)
        node = node_templates.get(search_node)
        self.assertIsNotNone(node)
        return node

    def get_relation(self, template, search_relation):
        self.assertIsNotNone(template.get(TOPOLOGY_TEMPLATE))
        relationship_templates = template.get(TOPOLOGY_TEMPLATE).get(RELATIONSHIP_TEMPLATES)
        self.assertIsNotNone(relationship_templates)
        relation = relationship_templates.get(search_relation)
        self.assertIsNotNone(relation)
        return relation

    def get_provider_template_output(self, template, template_filename=None, extra=None, delete_template=True,
                                  host_ip_parameter='public_address', return_extra_vars=False, test_name=None):
        if not template_filename:
            template_filename = self.template_filename()
        self.write_template(self.prepare_yaml(template))
        r, extra = common_translate(template_filename, False, self.PROVIDER, ANSIBLE, TEST, is_delete=False, extra=extra,
                             log_level='debug', host_ip_parameter=host_ip_parameter)
        if delete_template:
            self.delete_template(template_filename)
        print(yaml.dump(r))
        with open(os.path.join('testing', 'examples', test_name + '_' + self.PROVIDER + '.yaml'), 'w+') as f:
            print(yaml.dump(r), file=f)
        if return_extra_vars:
            return r, extra
        return r

    def update_node_template(self, template, node_name, update_value, param_type):
        update_value = {
            TOPOLOGY_TEMPLATE: {
                NODE_TEMPLATES: {
                    node_name: {
                        param_type: update_value
                    }
                }
            }
        }
        return deep_update_dict(template, update_value)

    def update_template_property(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, PROPERTIES)

    def update_template_interfaces(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, INTERFACES)

    def update_template_attribute(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, PROPERTIES)

    def update_template_capability(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, CAPABILITIES)

    def update_template_capability_properties(self, template, node_name, capability_name, update_value):
        uupdate_value = {
            capability_name: {
                PROPERTIES: update_value
            }
        }
        return self.update_template_capability(template, node_name, uupdate_value)

    def update_template_requirement(self, template, node_name, update_value):
        return self.update_node_template(template, node_name, update_value, REQUIREMENTS)

    def diff_files(self, file_name1, file_name2):
        with open(file_name1, 'r') as file1, open(file_name2, 'r') as file2:
            text1 = file1.readlines()
            text2 = file2.readlines()
            for line in difflib.unified_diff(text1, text2):
                print(line)


class TestProvider(BaseProvider):
    def test_meta(self, extra=None):
        if hasattr(self, 'check_meta'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "master=true"
            testing_parameter = {
                "meta": testing_value
            }

            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            provider_template = self.get_provider_template_output(template, extra=extra, test_name=self.test_meta.__name__)

            if extra:
                self.check_meta(provider_template, testing_value=testing_value, extra=extra)
            else:
                self.check_meta(provider_template, testing_value=testing_value)

    def test_private_address(self):
        if hasattr(self, 'check_private_address'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "192.168.12.26"
            testing_parameter = {
                "private_address": testing_value
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_private_address.__name__)

            self.check_private_address(provider_template, testing_value)

    def test_public_address(self):
        if hasattr(self, 'check_public_address'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "10.10.18.217"
            testing_parameter = {
                "public_address": testing_value
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_public_address.__name__)

            self.check_public_address(provider_template, testing_value)

    def test_network_name(self):
        if hasattr(self, 'check_network_name'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "test-two-routers"
            testing_parameter = {
                "networks": {
                    "default": {
                        "network_name": testing_value
                    }
                }
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_network_name.__name__)

            self.check_network_name(provider_template, testing_value)

    def test_host_capabilities(self):
        if hasattr(self, 'check_host_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "num_cpus": 1,
                "disk_size": "5 GiB",
                "mem_size": "1 GiB"
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, "host", testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_host_capabilities.__name__)

            self.check_host_capabilities(provider_template, testing_parameter)

    def test_endpoint_capabilities(self):
        if hasattr(self, 'check_endpoint_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "endpoint": {
                    "properties": {
                        "protocol": "tcp",
                        "port": 22,
                        "initiator": "target",
                        "ip_address": "0.0.0.0/0"
                    }
                }
            }
            template = self.update_template_capability(template, self.NODE_NAME, testing_parameter)
            provider_template, extra = self.get_provider_template_output(template, return_extra_vars=True, test_name=self.test_endpoint_capabilities.__name__)

            self.check_endpoint_capabilities(provider_template, extra)

    def test_os_capabilities(self):
        if hasattr(self, 'check_os_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "architecture": "x86_64",
                "type": "ubuntu",
                "distribution": "xenial",
                "version": 16.04
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, "os", testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_os_capabilities.__name__)

            self.check_os_capabilities(provider_template)

    def test_scalable_capabilities(self):
        if hasattr(self, 'check_scalable_capabilities'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "min_instances": 1,
                "default_instances": 2,
                "max_instances": 2
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, "scalable",
                                                                  testing_parameter)
            provider_template, extra = self.get_provider_template_output(template, return_extra_vars=True, test_name=self.test_scalable_capabilities.__name__)

            testing_value = '2'
            self.check_scalable_capabilities(provider_template, extra, testing_value)

    def test_host_of_software_component(self):
        if hasattr(self, "check_host_of_software_component"):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "public_address": "10.100.149.15",
                "networks": {
                    "default": {
                        "network_name": "net-for-intra-sandbox"
                    }
                }
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            testing_parameter = {
                "architecture": "x86_64",
                "type": "ubuntu",
                "distribution": "xenial",
                "version": 16.04
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, "os", testing_parameter)
            template['node_types'] = {
                'clouni.nodes.ServerExample': {
                    'derived_from': 'tosca.nodes.SoftwareComponent'
                }
            }
            template['topology_template']['node_templates']['service_1'] = {
                'type': 'clouni.nodes.ServerExample',
                'properties': {
                    'component_version': 0.1
                },
                'requirements': [{
                    'host': self.NODE_NAME
                }],
                'interfaces':{
                    'Standard': {
                        'create': {
                            'implementation': 'testing/examples/ansible-server-example.yaml',
                            'inputs': {
                                'version': { 'get_property': ['service_1', 'component_version'] }
                            }
                        }
                    }
                }
            }
            provider_template = self.get_provider_template_output(template, test_name=self.test_host_of_software_component.__name__)
            testing_value = 'service_1_server_example'
            self.check_host_of_software_component(provider_template, testing_value)

    def test_get_input(self):
        if hasattr(self, 'check_get_input'):
            testing_value = "10.100.157.20"
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            template['topology_template']['inputs'] = {
                'public_address': {
                    'type': 'string',
                    'default': testing_value
                }
            }
            testing_parameter = {
                "public_address": {
                    "get_input": "public_address"
                }
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_get_input.__name__)

            self.check_get_input(provider_template, testing_value)

    def test_get_property(self):
        if hasattr(self, 'check_get_property'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "master=true"
            testing_parameter = {
                "meta": testing_value
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            template['topology_template']['node_templates'][self.NODE_NAME + '_2'] = {
                'type': 'tosca.nodes.Compute',
                'properties': {
                    'meta': {
                        'get_property': [
                            self.NODE_NAME,
                            'meta'
                        ]
                    }
                }
            }
            provider_template = self.get_provider_template_output(template, test_name=self.test_get_property.__name__)

            self.check_get_property(provider_template, testing_value)

    def test_get_attribute(self):
        if hasattr(self, 'check_get_attribute'):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "master=true"
            testing_parameter = {
                "meta": testing_value
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            template['topology_template']['node_templates'][self.NODE_NAME + '_2'] = {
                'type': 'tosca.nodes.Compute',
                'properties': {
                    'meta': {
                        'get_attribute': [
                            self.NODE_NAME,
                            'meta'
                        ]
                    }
                }
            }
            provider_template = self.get_provider_template_output(template, test_name=self.test_get_attribute.__name__)

            self.check_get_attribute(provider_template, testing_value)

    def test_outputs(self):
        if hasattr(self, "check_outputs"):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = "10.10.18.217"
            testing_parameter = {
                "public_address": testing_value
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            template['topology_template']['outputs'] = {
                "server_address": {
                    "description": "Public IP address for the provisioned server.",
                    "value": {
                        "get_attribute": [ self.NODE_NAME, "public_address" ] }
                }
            }
            provider_template = self.get_provider_template_output(template, test_name=self.test_outputs.__name__)

            self.check_outputs(provider_template, testing_value)

    def test_multiple_relationships(self):
        if hasattr(self, "check_public_address") and hasattr(self, "check_private_address"):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_parameter = {
                "public_address": "10.100.115.15",
                "private_address": "192.168.12.25"
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            provider_template = self.get_provider_template_output(template, test_name=self.test_multiple_relationships.__name__)

            self.check_public_address(provider_template, "10.100.115.15")
            self.check_private_address(provider_template, "192.168.12.25")

    def test_host_ip_parameter(self):
        if hasattr(self, "check_host_ip_parameter"):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = 'net-for-sandbox'
            testing_parameter = {
                "public_address": "10.100.156.76",
                "private_address": "192.168.34.34",
                "networks": {
                    "default": {
                        "network_name": testing_value
                    }
                },
                "ports": {
                    "extra": {
                        "port_name": "extra_port"
                    }
                }
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            testing_parameter = {
                "architecture": "x86_64",
                "type": "cirros",
                "version": "0.4.0"
            }
            template = self.update_template_capability_properties(template, self.NODE_NAME, 'os', testing_parameter)
            provider_template = self.get_provider_template_output(template, host_ip_parameter='networks.default', test_name=self.test_host_ip_parameter.__name__)

            self.check_host_ip_parameter(provider_template, testing_value)

    def test_nodes_interfaces_operations(self):
        if hasattr(self, "check_nodes_interfaces_operations"):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = 'test'
            testing_parameter = {
                'Standard': {
                    'stop': {
                        'implementation': 'testing/examples/ansible-operation-example.yaml',
                        'inputs': {
                            testing_value: testing_value
                        }
                    },
                    'start': {
                        'implementation': 'testing/examples/ansible-operation-example.yaml',
                        'inputs': {
                            testing_value: testing_value
                        }
                    },
                    'configure': {
                        'implementation': 'testing/examples/ansible-operation-example.yaml',
                        'inputs': {
                            testing_value: testing_value
                        }
                    }
                }
            }
            template = self.update_template_interfaces(template, self.NODE_NAME, testing_parameter)
            testing_parameter = {
                "public_address": "10.10.18.217"
            }
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)

            provider_template = self.get_provider_template_output(template, host_ip_parameter='public_address', test_name=self.test_nodes_interfaces_operations.__name__)

            self.check_nodes_interfaces_operations(provider_template, testing_value)

    def test_relationships_interfaces_operations(self):
        if hasattr(self, "check_relationships_interfaces_operations"):
            template = copy.deepcopy(self.DEFAULT_TEMPLATE)
            testing_value = 'test'
            testing_parameter = {
                "public_address": "10.10.18.217"
            }
            rel_name = 'test_relationship'
            soft_name = 'service_1'
            template = self.update_template_property(template, self.NODE_NAME, testing_parameter)
            testing_parameter = {
                'Standard': {
                    'configure': {
                        'implementation': 'testing/examples/ansible-operation-example.yaml',
                        'inputs': {
                            testing_value: testing_value
                        }
                    }
                }
            }
            template = self.update_template_interfaces(template, self.NODE_NAME, testing_parameter)
            template['node_types'] = {
                'clouni.nodes.ServerExample': {
                    'derived_from': 'tosca.nodes.SoftwareComponent'
                }
            }
            template['topology_template']['node_templates'][soft_name] = {
                'type': 'clouni.nodes.ServerExample',
                'properties': {
                    'component_version': 0.1
                },
                'requirements': [{
                    'host': {
                        'node': self.NODE_NAME,
                        'relationship': rel_name
                    }
                }],
                'interfaces': {
                    'Standard': {
                        'create': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                 testing_value: testing_value
                            }
                        },
                        'configure': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                 testing_value: testing_value
                            }
                        }
                    }
                }
            }
            template['topology_template']['relationship_templates'] = {}
            template['topology_template']['relationship_templates'][rel_name] = {
                'type': 'tosca.relationships.HostedOn',
                'interfaces': {
                    'Configure': {
                        'pre_configure_target': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                testing_value: testing_value
                            }
                        },
                        'post_configure_target': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                testing_value: testing_value
                            }
                        },
                        'pre_configure_source': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                testing_value: testing_value
                            }
                        },
                        'post_configure_source': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                testing_value: testing_value
                            }
                        },
                        'add_source': {
                            'implementation': 'testing/examples/ansible-operation-example.yaml',
                            'inputs': {
                                testing_value: testing_value
                            }
                        }
                    }
                }
            }
            provider_template = self.get_provider_template_output(template, host_ip_parameter='public_address', test_name=self.test_relationships_interfaces_operations.__name__)

            self.check_relationships_interfaces_operations(provider_template, rel_name, soft_name, testing_value)