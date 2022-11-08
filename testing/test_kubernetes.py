import unittest
import copy
import os

from toscaparser.common.exception import MissingRequiredFieldError, ValidationError
from testing.base import BaseProvider
from provider_tool.common.tosca_reserved_keys import TOSCA_DEFINITIONS_VERSION, TOPOLOGY_TEMPLATE, NODE_TEMPLATES, \
    TYPE, CAPABILITIES, PROPERTIES

from provider_tool.common.utils import get_project_root_path


class TestKubernetesOutput(unittest.TestCase, BaseProvider):
    PROVIDER = 'kubernetes'
    NODE_NAME = 'server-master'
    DEFAULT_TEMPLATE = {
        TOSCA_DEFINITIONS_VERSION: "tosca_simple_yaml_1_0",
        TOPOLOGY_TEMPLATE: {
            NODE_TEMPLATES: {
                NODE_NAME: {
                    TYPE: "tosca.nodes.Compute",
                    CAPABILITIES: {
                        'os': {
                            PROPERTIES: {
                                'type': 'ubuntu',
                                'distribution': 'xenial'
                            }
                        }
                    }
                }
            }
        }
    }
