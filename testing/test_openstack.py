import unittest
from provider_tool.common.tosca_reserved_keys import *
from provider_tool.providers.common.python_sources import transform_units

from provider_tool.common import utils

from testing.base import TestProvider

import copy, os, re, yaml

class TestOpenStackOutput (unittest.TestCase, TestProvider):
    PROVIDER = 'openstack'
    COMPUTE = '_server'
    SEC_GROUP = '_security_group'
    SEC_GROUP_RULE = '_security_group_rule'
    SUBNET = '_subnet'
    NETWORK = '_network'
    PORT = '_port'
    FIP = '_floating_ip'

    def check_compute_module(self, task, port_name):
        assert False

    def check_network_module(self, task):
        assert False

    def check_port_module(self, task, subnet_name):
        assert False

    def check_subnet_module(self, task, network_name):
        assert False

    def test_server_name(self):
        template = copy.deepcopy(self.DEFAULT_TEMPLATE)
        provider_template = self.get_provider_template_output(template)

        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get('properties'))
        self.assertEqual(server.get('properties').get('name'), self.NODE_NAME)

    def test_meta(self, extra=None):
        super(TestOpenStackOutput, self).test_meta(extra=extra)

    def check_meta(self, provider_template, testing_value=None, extra=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertEqual(server.get(PROPERTIES).get('meta'), testing_value)

    def test_private_address(self):
        super(TestOpenStackOutput, self).test_private_address()

    def check_private_address(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('nics'))

        checked = False
        for elem in server.get(PROPERTIES).get('nics'):
            self.assertIsInstance(elem, dict)
            if self.NODE_NAME + self.PORT in elem.get('port-name'):
                checked = True

        self.assertTrue(checked)

        port = self.get_node(provider_template, self.NODE_NAME + self.PORT)
        self.assertIsNotNone(port.get(PROPERTIES))
        self.assertIsNotNone(port.get(PROPERTIES).get('fixed_ips'))

        checked = False
        for elem in port.get(PROPERTIES).get('fixed_ips'):
            self.assertIsInstance(elem, dict)
            if 'ip_address' in elem:
                checked = True
                self.assertEqual(elem.get('ip_address'), testing_value)

        self.assertTrue(checked)

    def test_public_address(self):
        super(TestOpenStackOutput, self).test_public_address()

    def check_public_address(self, provider_template, testing_value=None):
        fip = self.get_node(provider_template, self.NODE_NAME + self.FIP)
        self.assertIsNotNone(fip.get(PROPERTIES))
        self.assertEquals(fip.get(PROPERTIES).get('floating_ip_address'), testing_value)

        checked_1 = False
        checked_2 = False
        self.assertIsNotNone(fip.get(REQUIREMENTS))
        for elem in fip.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'server' in elem:
                checked_2 = True
                self.assertEqual(elem.get('server').get('node'), self.NODE_NAME + self.COMPUTE)
            if 'network' in elem:
                checked_1 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

    def test_network_name(self):
        super(TestOpenStackOutput, self).test_network_name()

    def check_network_name(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('nics'))

        checked = False
        for elem in server.get(PROPERTIES).get('nics'):
            self.assertIsInstance(elem, dict)
            if 'net-name' in elem:
                checked = True
                self.assertEqual(elem.get('net-name'), testing_value)

        self.assertTrue(checked)

    def test_host_capabilities(self):
        super(TestOpenStackOutput, self).test_host_capabilities()

    def check_host_capabilities(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(REQUIREMENTS))
        checked_1 = False
        checked_2 = False
        checked_3 = False

        for elem in server.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'flavor' in elem:
                self.assertIsNotNone(elem.get('flavor').get(NODE_FILTER))
                self.assertIsNotNone(elem.get('flavor').get(NODE_FILTER).get(PROPERTIES))
                for item in elem.get('flavor').get(NODE_FILTER).get(PROPERTIES):
                    self.assertIsInstance(item, dict)
                    if 'disk' in item:
                        self.assertEqual(transform_units(testing_value['disk_size'], 'GiB', is_only_numb=True), item.get('disk'))
                        checked_1 = True
                    if 'vcpus' in item:
                        self.assertEqual(testing_value['num_cpus'], item.get('vcpus'))
                        checked_2 = True
                    if 'ram' in item:
                        self.assertEqual(transform_units(testing_value['mem_size'], 'MiB', is_only_numb=True), item.get('ram'))
                        checked_3 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)
        self.assertTrue(checked_3)

    def test_endpoint_capabilities(self):
        super(TestOpenStackOutput, self).test_endpoint_capabilities()

    def check_endpoint_capabilities(self, provider_template, extra, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(REQUIREMENTS))
        checked = False

        for elem in server.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'security_groups' in elem:
                self.assertEqual(elem.get('security_groups').get(NODE), self.NODE_NAME + self.SEC_GROUP)
                checked = True

        self.assertTrue(checked)

        sec_gr = self.get_node(provider_template, self.NODE_NAME + self.SEC_GROUP)
        sec_rule = self.get_node(provider_template, self.NODE_NAME + self.SEC_GROUP_RULE)

        self.assertIsNotNone(sec_rule.get(REQUIREMENTS))
        checked = False

        for elem in sec_rule.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'security_group' in elem:
                self.assertEqual(elem.get('security_group').get(NODE), self.NODE_NAME + self.SEC_GROUP)
                checked = True

        self.assertIsInstance(sec_rule.get(PROPERTIES), dict)
        self.assertEqual(sec_rule.get(PROPERTIES).get('remote_ip_prefix'), '0.0.0.0/0')

        self.assertTrue(checked)

        self.assertIsInstance(extra.get(self.NODE_NAME + self.SEC_GROUP_RULE), dict)
        self.assertIsInstance(extra.get(self.NODE_NAME + self.SEC_GROUP_RULE).get('vars'), dict)

        self.assertListEqual(extra.get(self.NODE_NAME + self.SEC_GROUP_RULE).get('vars').get('protocol'), ['tcp'])
        self.assertListEqual(extra.get(self.NODE_NAME + self.SEC_GROUP_RULE).get('vars').get('port'), [22])
        self.assertListEqual(extra.get(self.NODE_NAME + self.SEC_GROUP_RULE).get('vars').get('initiator'), ['ingress'])

    def test_os_capabilities(self):
        super(TestOpenStackOutput, self).test_os_capabilities()

    def check_os_capabilities(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(REQUIREMENTS))
        checked_1 = False
        checked_2 = False

        for elem in server.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'image' in elem:
                self.assertIsNotNone(elem.get('image').get(NODE_FILTER))
                self.assertIsNotNone(elem.get('image').get(NODE_FILTER).get(PROPERTIES))
                for item in elem.get('image').get(NODE_FILTER).get(PROPERTIES):
                    self.assertIsInstance(item, dict)
                    if PARAMETER in item:
                        checked_1 = True
                        self.assertEqual(item.get(PARAMETER), 'name')
                    if VALUE in item:
                        checked_2 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

    def test_multiple_relationships(self):
        super(TestOpenStackOutput, self).test_multiple_relationships()

    def test_scalable_capabilities(self):
        super(TestOpenStackOutput, self).test_scalable_capabilities()

    def check_scalable_capabilities(self, provider_template, extra, testing_value):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get('properties'))
        self.assertEqual(server.get('properties').get('name'), self.NODE_NAME + '_{{ item }}')

        self.assertIsInstance(extra.get(self.NODE_NAME + self.COMPUTE), dict)
        self.assertTrue('end=' + testing_value in extra.get(self.NODE_NAME + self.COMPUTE).get('with_sequence'))

    def test_host_of_software_component(self):
        super(TestOpenStackOutput, self).test_host_of_software_component()

    def check_host_of_software_component(self, provider_template, testing_value):
        fip = self.get_node(provider_template, self.NODE_NAME + self.FIP)
        self.assertIsNotNone(fip.get(PROPERTIES))
        self.assertIsNotNone(fip.get(PROPERTIES).get('floating_ip_address'))

        checked_1 = False
        checked_2 = False
        self.assertIsNotNone(fip.get(REQUIREMENTS))
        for elem in fip.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'server' in elem:
                checked_2 = True
                self.assertEqual(elem.get('server').get(NODE), self.NODE_NAME + self.COMPUTE)
            if 'network' in elem:
                checked_1 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

        checked_1 = False
        checked_2 = False

        software = self.get_node(provider_template, testing_value)
        self.assertIsNotNone(software.get(REQUIREMENTS))
        for elem in software.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'host' in elem:
                checked_2 = True
                self.assertEqual(elem.get('host').get(NODE), self.NODE_NAME + self.COMPUTE)
            if 'dependency' in elem:
                if elem.get('dependency').get(NODE) == self.NODE_NAME + self.FIP:
                    checked_1 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)


    def test_get_property(self):
        super(TestOpenStackOutput, self).test_get_property()

    def check_get_property(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertEqual(server.get(PROPERTIES).get('meta'), testing_value)

        server_2 = self.get_node(provider_template, self.NODE_NAME + '_2' + self.COMPUTE)
        self.assertIsNotNone(server_2.get(PROPERTIES))
        self.assertEqual(server_2.get(PROPERTIES).get('meta'), testing_value)

    def test_host_ip_parameter(self):
        super(TestOpenStackOutput, self).test_host_ip_parameter()

    def check_host_ip_parameter(self, provider_template, testing_value):
        fip = self.get_node(provider_template, self.NODE_NAME + self.FIP)
        self.assertIsNotNone(fip.get(PROPERTIES))
        self.assertIsNotNone(fip.get(PROPERTIES).get('floating_ip_address'))

        checked_1 = False
        checked_2 = False
        self.assertIsNotNone(fip.get(REQUIREMENTS))
        for elem in fip.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'server' in elem:
                checked_2 = True
                self.assertEqual(elem.get('server').get('node'), self.NODE_NAME + self.COMPUTE)
            if 'network' in elem:
                checked_1 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('nics'))

        self.assertIsInstance(server.get(PROPERTIES).get('nics'), list)
        self.assertTrue(len(server.get(PROPERTIES).get('nics')) > 0)

        checked_1 = False
        checked_2 = False
        for elem in server.get(PROPERTIES).get('nics'):
            self.assertIsInstance(elem, dict)
            if elem.get('port-name'):
                if self.NODE_NAME + self.PORT in elem.get('port-name'):
                    checked_1 = True
                if elem.get('port-name') == 'extra_port':
                    checked_2 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

        # the most important string
        self.assertEqual(server.get(PROPERTIES).get('nics')[0].get('net-name'), testing_value)

        port = self.get_node(provider_template, self.NODE_NAME + self.PORT)
        self.assertIsNotNone(port.get(PROPERTIES))
        self.assertIsNotNone(port.get(PROPERTIES).get('fixed_ips'))

        checked = False
        for elem in port.get(PROPERTIES).get('fixed_ips'):
            self.assertIsInstance(elem, dict)
            if 'ip_address' in elem:
                checked = True

        self.assertTrue(checked)



    def test_nodes_interfaces_operations(self):
        super(TestOpenStackOutput, self).test_nodes_interfaces_operations()

    def check_nodes_interfaces_operations(self, provider_template, testing_value):
        server = self.get_default_node(provider_template)
        self.assertIsInstance(server.get(INTERFACES), dict)
        standard = server.get(INTERFACES).get('Standard')
        self.assertIsInstance(standard, dict)

        checked_1 = False
        checked_2 = False
        checked_3 = False

        for op in standard:
            if op == 'configure':
                self.assertIsInstance(standard[op], dict)
                self.assertEqual(standard[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(standard[op].get('inputs'), {testing_value: testing_value})
                checked_1 = True
            if op == 'stop':
                self.assertIsInstance(standard[op], dict)
                self.assertEqual(standard[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(standard[op].get('inputs'), {testing_value: testing_value})
                checked_2 = True
            if op == 'start':
                self.assertIsInstance(standard[op], dict)
                self.assertEqual(standard[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(standard[op].get('inputs'), {testing_value: testing_value})
                checked_3 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)
        self.assertTrue(checked_3)

    def test_relationships_interfaces_operations(self):
        super(TestOpenStackOutput, self).test_relationships_interfaces_operations()

    def check_relationships_interfaces_operations(self, provider_template, rel_name, soft_name, testing_value):
        server = self.get_default_node(provider_template)
        self.assertIsInstance(server.get(INTERFACES), dict)
        standard = server.get(INTERFACES).get('Standard')
        self.assertIsInstance(standard, dict)

        checked = False

        for op in standard:
            if op == 'configure':
                self.assertIsInstance(standard[op], dict)
                self.assertEqual(standard[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(standard[op].get('inputs'), {testing_value: testing_value})
                checked = True

        self.assertTrue(checked)

        self.assertIsInstance(provider_template.get(NODE_TYPES), dict)

        soft = self.get_node(provider_template, soft_name + "_server_example")

        self.assertIsInstance(soft.get(INTERFACES), dict)
        standard = soft.get(INTERFACES).get('Standard')
        self.assertIsInstance(standard, dict)

        checked_1 = False
        checked_2 = False

        for op in standard:
            if op == 'configure':
                self.assertIsInstance(standard[op], dict)
                self.assertEqual(standard[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(standard[op].get('inputs'), {testing_value: testing_value})
                checked_1 = True
            if op == 'create':
                self.assertIsInstance(standard[op], dict)
                self.assertEqual(standard[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(standard[op].get('inputs'), {testing_value: testing_value})
                checked_2 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

        rel = self.get_relation(provider_template, rel_name + "_hosted_on")

        self.assertIsInstance(rel.get(INTERFACES), dict)
        conf = rel.get(INTERFACES).get('Configure')
        self.assertIsInstance(conf, dict)

        checked_1 = False
        checked_2 = False
        checked_3 = False
        checked_4 = False
        checked_5 = False

        for op in conf:
            if op == 'add_source':
                self.assertIsInstance(conf[op], dict)
                self.assertEqual(conf[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(conf[op].get('inputs'), {testing_value: testing_value})
                checked_1 = True
            if op == 'post_configure_source':
                self.assertIsInstance(conf[op], dict)
                self.assertEqual(conf[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(conf[op].get('inputs'), {testing_value: testing_value})
                checked_2 = True
            if op == 'post_configure_target':
                self.assertIsInstance(conf[op], dict)
                self.assertEqual(conf[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(conf[op].get('inputs'), {testing_value: testing_value})
                checked_3 = True
            if op == 'pre_configure_source':
                self.assertIsInstance(conf[op], dict)
                self.assertEqual(conf[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(conf[op].get('inputs'), {testing_value: testing_value})
                checked_4 = True
            if op == 'pre_configure_target':
                self.assertIsInstance(conf[op], dict)
                self.assertEqual(conf[op].get('implementation'), 'testing/examples/ansible-operation-example.yaml')
                self.assertEqual(conf[op].get('inputs'), {testing_value: testing_value})
                checked_5 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)
        self.assertTrue(checked_3)
        self.assertTrue(checked_4)
        self.assertTrue(checked_5)
