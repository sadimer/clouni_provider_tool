import unittest

from provider_tool.providers.common.python_sources import transform_units

from provider_tool.common.tosca_reserved_keys import *

from testing.base import TestProvider
import copy, os, yaml

PUBLIC_ADDRESS = 'public_address'

class TestAmazonOutput (unittest.TestCase, TestProvider):
    PROVIDER = 'amazon'
    COMPUTE = '_instance'
    SEC_GROUP = '_group'
    SUBNET = '_subnet'
    NETWORK = '_vpc_net'
    PORT = '_eni'

    def test_server_name(self):
        template = copy.deepcopy(self.DEFAULT_TEMPLATE)
        provider_template = self.get_provider_template_output(template)

        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertEqual(server.get(PROPERTIES).get('name'), self.NODE_NAME)

    def test_meta(self, extra=None):
        super(TestAmazonOutput, self).test_meta(extra=extra)

    def check_meta (self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('tags'))
        self.assertEqual(server.get(PROPERTIES).get('tags').get('metadata'), testing_value)

    def test_multiple_relationships(self):
        super(TestAmazonOutput, self).test_multiple_relationships()

    def test_private_address(self):
        super(TestAmazonOutput, self).test_private_address()

    def check_private_address(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('network'))
        self.assertEqual(server.get(PROPERTIES).get('network').get('private_ip_address'), testing_value)

    def check_network_name(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(REQUIREMENTS))
        checked_1 = False
        checked_2 = False

        for elem in server.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'vpc_subnet_id' in elem:
                self.assertIsNotNone(elem.get('vpc_subnet_id').get(NODE_FILTER))
                self.assertIsNotNone(elem.get('vpc_subnet_id').get(NODE_FILTER).get(PROPERTIES))
                for item in elem.get('vpc_subnet_id').get(NODE_FILTER).get(PROPERTIES):
                    self.assertIsInstance(item, dict)
                    if PARAMETER in item:
                        checked_1 = True
                        self.assertEqual(item.get(PARAMETER), ID)
                    if VALUE in item:
                        checked_2 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

    def test_host_capabilities(self):
        super(TestAmazonOutput, self).test_host_capabilities()

    def check_host_capabilities(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(REQUIREMENTS))
        checked_1 = False
        checked_2 = False
        checked_3 = False

        for elem in server.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'instance_type' in elem:
                self.assertIsNotNone(elem.get('instance_type').get(NODE_FILTER))
                self.assertIsNotNone(elem.get('instance_type').get(NODE_FILTER).get(PROPERTIES))
                for item in elem.get('instance_type').get(NODE_FILTER).get(PROPERTIES):
                    self.assertIsInstance(item, dict)
                    if 'storage' in item:
                        self.assertEqual(transform_units(testing_value['disk_size'], 'GiB', is_only_numb=True), item.get('storage'))
                        checked_1 = True
                    if 'vcpus' in item:
                        self.assertEqual(testing_value['num_cpus'], item.get('vcpus'))
                        checked_2 = True
                    if 'memory' in item:
                        self.assertEqual(transform_units(testing_value['mem_size'], 'GiB', is_only_numb=True), item.get('memory'))
                        checked_3 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)
        self.assertTrue(checked_3)

    def test_endpoint_capabilities(self):
        super(TestAmazonOutput, self).test_endpoint_capabilities()

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

        self.assertIsInstance(sec_gr.get(PROPERTIES), dict)
        self.assertIsInstance(sec_gr.get(PROPERTIES).get('rules'), list)

        checked = False

        for elem in sec_gr.get(PROPERTIES).get('rules'):
            if elem.get('cidr_ip') == '0.0.0.0/0' and elem.get('ports') == [22] and elem.get('proto') == 'tcp':
                checked = True

        self.assertTrue(checked)

    def test_os_capabilities(self):
        super(TestAmazonOutput, self).test_os_capabilities()

    def check_os_capabilities(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(REQUIREMENTS))
        checked_1 = False
        checked_2 = False

        for elem in server.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'image_id' in elem:
                self.assertIsNotNone(elem.get('image_id').get(NODE_FILTER))
                self.assertIsNotNone(elem.get('image_id').get(NODE_FILTER).get(PROPERTIES))
                for item in elem.get('image_id').get(NODE_FILTER).get(PROPERTIES):
                    self.assertIsInstance(item, dict)
                    if PARAMETER in item:
                        checked_1 = True
                        self.assertEqual(item.get(PARAMETER), 'image_id')
                    if VALUE in item:
                        checked_2 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

    def test_network_name(self):
        super(TestAmazonOutput, self).test_network_name()

    def test_host_capabilities(self):
        super(TestAmazonOutput, self).test_host_capabilities()

    def test_get_property(self):
        super(TestAmazonOutput, self).test_get_property()

    def check_get_property(self, provider_template, testing_value=None):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('tags'))
        self.assertEqual(server.get(PROPERTIES).get('tags').get('metadata'), testing_value)

        server_2 = self.get_node(provider_template, self.NODE_NAME + '_2' + self.COMPUTE)
        self.assertIsNotNone(server_2.get(PROPERTIES))
        self.assertIsNotNone(server_2.get(PROPERTIES).get('tags'))
        self.assertEqual(server_2.get(PROPERTIES).get('tags').get('metadata'), testing_value)

    def test_host_of_software_component(self):
        super(TestAmazonOutput, self).test_host_of_software_component()

    def check_host_of_software_component(self, provider_template, testing_value):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get(PROPERTIES))
        self.assertIsNotNone(server.get(PROPERTIES).get('network'))
        self.assertTrue(server.get(PROPERTIES).get('network').get('assign_public_ip'))

        checked_1 = False
        checked_2 = False

        software = self.get_node(provider_template, testing_value)
        self.assertIsNotNone(software.get(REQUIREMENTS))
        for elem in software.get(REQUIREMENTS):
            self.assertIsInstance(elem, dict)
            if 'host' in elem:
                checked_2 = True
                self.assertEqual(elem.get('host').get('node'), self.NODE_NAME + self.COMPUTE)
            if 'dependency' in elem:
                if elem.get('dependency').get('node') == self.NODE_NAME + self.COMPUTE:
                    checked_1 = True

        self.assertTrue(checked_1)
        self.assertTrue(checked_2)

    def test_nodes_interfaces_operations(self):
        super(TestAmazonOutput, self).test_nodes_interfaces_operations()

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

    def test_scalable_capabilities(self):
        super(TestAmazonOutput, self).test_scalable_capabilities()

    def check_scalable_capabilities(self, provider_template, extra, testing_value):
        server = self.get_default_node(provider_template)
        self.assertIsNotNone(server.get('properties'))
        self.assertEqual(server.get('properties').get('name'), self.NODE_NAME + '_{{ item }}')

        self.assertIsInstance(extra.get(self.NODE_NAME + self.COMPUTE), dict)
        self.assertTrue('end=' + testing_value in extra.get(self.NODE_NAME + self.COMPUTE).get('with_sequence'))

    def test_relationships_interfaces_operations(self):
        super(TestAmazonOutput, self).test_relationships_interfaces_operations()

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
