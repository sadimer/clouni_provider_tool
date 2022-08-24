from toscaparser.imports import ImportsLoader
from toscaparser.topology_template import TopologyTemplate
from toscaparser.functions import GetProperty

from provider_tool.common import utils
from provider_tool.common.tosca_reserved_keys import *

from provider_tool.providers.common.provider_configuration import ProviderConfiguration
from provider_tool.providers.common.translator_to_provider import translate as translate_to_provider


import os, copy, json, yaml, logging, sys, six

SEPARATOR = ':'

class ProviderToscaTemplate(object):
    REQUIRED_CONFIG_PARAMS = (TOSCA_ELEMENTS_MAP_FILE, TOSCA_ELEMENTS_DEFINITION_FILE)
    DEPENDENCY_FUNCTIONS = (GET_PROPERTY, GET_ATTRIBUTE, GET_OPERATION_OUTPUT)
    DEFAULT_ARTIFACTS_DIRECTOR = ARTIFACTS

    def __init__(self, tosca_parser_template_object, provider, configuration_tool, cluster_name, host_ip_parameter, public_key_path,
                 is_delete, common_map_files=[]):
        self.provider = provider
        self.is_delete = is_delete
        self.host_ip_parameter = host_ip_parameter
        self.public_key_path = public_key_path
        self.configuration_tool = configuration_tool
        self.provider_config = ProviderConfiguration(self.provider)
        self.cluster_name = cluster_name
        for sec in self.REQUIRED_CONFIG_PARAMS:
            if not self.provider_config.config[self.provider_config.MAIN_SECTION].get(sec):
                logging.error("Provider configuration parameter \'%s\' has missing value" % sec)
                logging.error("Translating failed")
                raise Exception("Provider configuration parameter \'%s\' has missing value" % sec)

        map_files = self.provider_config.get_section(self.provider_config.MAIN_SECTION) \
            .get(TOSCA_ELEMENTS_MAP_FILE)
        if isinstance(map_files, six.string_types):
            map_files = [map_files]
        tosca_elements_map_files = []
        for file in map_files:
            map_file = file
            if not os.path.isabs(file):
                map_file = os.path.join(self.provider_config.config_directory, file)
            tosca_elements_map_files.append(map_file)

        self.map_files = common_map_files
        self.map_files.extend(tosca_elements_map_files)
        for file in self.map_files:
            if not os.path.isfile(file):
                logging.error("Mapping file for provider %s not found: %s" % (self.provider, file))
                raise Exception("Mapping file for provider %s not found: %s" % (self.provider, file))

        topology_template = tosca_parser_template_object.topology_template
        self.inputs = topology_template.tpl.get(INPUTS, {})
        self.outputs = topology_template.tpl.get(OUTPUTS, {})
        self.definitions = topology_template.custom_defs

        self.node_templates = {}
        self.relationship_templates = {}
        self.template_mapping = {}
        for tmpl in topology_template.nodetemplates:
            self.node_templates[tmpl.name] = tmpl.entity_tpl

        for tmpl in topology_template.relationship_templates:
            self.relationship_templates[tmpl.name] = tmpl.entity_tpl
        import_definition_file = ImportsLoader([self.definition_file()], None, list(SERVICE_TEMPLATE_KEYS),
                                               topology_template.tpl)
        self.definitions.update(import_definition_file.get_custom_defs())
        self.software_types = set()
        self.fulfil_definitions_with_parents()
        self.artifacts = []
        self.used_conditions_set = set()
        self.extra_configuration_tool_params = dict()
        self.make_extended_notations()
        self.node_templates = self.resolve_get_property_functions(self.node_templates)
        self.relationship_templates = self.resolve_get_property_functions(self.relationship_templates)

        # resolving template dependencies fo normative templates
        self.template_dependencies = dict()
        self._relation_target_source = dict()
        self.resolve_in_template_dependencies()

        self.normative_nodes_graph = self.normative_nodes_graph_dependency()

        self.translate_to_provider()
        self.make_extended_notations()
        self.add_dependency_requirements()

        self.dict_tpl = {TOPOLOGY_TEMPLATE: {}}
        if self.node_templates:
            self.dict_tpl[TOPOLOGY_TEMPLATE][NODE_TEMPLATES] = self.node_templates
        if self.relationship_templates:
            self.dict_tpl[TOPOLOGY_TEMPLATE][RELATIONSHIP_TEMPLATES] = self.relationship_templates
        if self.outputs:
            self.dict_tpl[TOPOLOGY_TEMPLATE][OUTPUTS] = self.outputs
        if self.inputs:
            self.dict_tpl[TOPOLOGY_TEMPLATE][INPUTS] = self.inputs
        self.dict_tpl[TOSCA_DEFINITIONS_VERSION] = tosca_parser_template_object.version

    def add_dependency_requirements(self):
        dependencies = self.translate_normative_graph()
        for key, value in dependencies.items():
            for elem in value:
                if elem not in self.node_templates:
                    logging.error('Unexpected values: node \'%s\' not in node templates' % elem)
                    raise Exception('Unexpected values: node \'%s\' not in node templates' % elem)
                if key not in self.node_templates:
                    logging.error('Unexpected values: node \'%s\' not in node templates' % key)
                    raise Exception('Unexpected values: node \'%s\' not in node templates' % key)
                if REQUIREMENTS not in self.node_templates[key]:
                    self.node_templates[key][REQUIREMENTS] = []
                self.node_templates[key][REQUIREMENTS].append({'dependency': {NODE: elem}})

    def translate_normative_graph(self):
        """
            This method translates dependencies from nodes of normative template into
            dependencies between nodes in provider template
        """
        dependencies = {}
        for temp, dep in self.normative_nodes_graph.items():
            for elem in dep:
                for key, val in self.template_mapping.items():
                    if elem == key:
                        for tpl in self.template_mapping[temp]:
                            for el_tpl in self.template_mapping[elem]:
                                if tpl not in dependencies:
                                    dependencies[tpl] = {el_tpl}
                                else:
                                    dependencies[tpl].add(el_tpl)
        return dependencies

    def normative_nodes_graph_dependency(self):
        """
            This method generates dict of nodes, sorted by
            dependencies from normative TOSCA templates
        """
        nodes = set(self.node_templates.keys())
        dependencies = {}
        for templ_name in nodes:
            set_intersection = nodes.intersection(self.template_dependencies.get(templ_name, set()))
            utils.deep_update_dict(dependencies, {templ_name: set_intersection})
        return dependencies

    def add_template_dependency(self, node_name, dependency_name):
        if not dependency_name == SELF and not node_name == dependency_name:
            if self.template_dependencies.get(node_name) is None:
                self.template_dependencies[node_name] = {dependency_name}
            else:
                self.template_dependencies[node_name].add(dependency_name)

    def resolve_in_template_dependencies(self):
        """
        TODO think through the logic to replace mentions by id
        Changes all mentions of node_templates by name in requirements, places dictionary with node_filter instead
        :return:
        """
        for node_name, node in self.node_templates.items():
            for req in node.get(REQUIREMENTS, []):
                for req_name, req_body in req.items():

                    # Valid keys are ('node', 'node_filter', 'relationship', 'capability', 'occurrences')
                    # Only node and relationship might be a template name or a type
                    req_relationship = req_body.get(RELATIONSHIP)
                    req_node = req_body.get(NODE)

                    if req_relationship is not None:
                        (_, _, type_name) = utils.tosca_type_parse(req_relationship)
                        if type_name is None:
                            self.add_template_dependency(node_name, req_relationship)
                            self._relation_target_source[req_relationship] = {
                                'source': node_name,
                                'target': req_node
                            }

                    if req_node is not None:
                        (_, _, type_name) = utils.tosca_type_parse(req_node)
                        if type_name is None:
                            self.add_template_dependency(node_name, req_node)

            node_types_from_requirements = set()
            req_definitions = self.definitions[node[TYPE]].get(REQUIREMENTS, [])
            for req in req_definitions:
                for req_name, req_def in req.items():
                    if req_def.get(NODE, None) is not None:
                        if req_def[NODE] != node[TYPE]:
                            node_types_from_requirements.add(req_def[NODE])
            for req_node_name, req_node_tmpl in self.node_templates.items():
                if req_node_tmpl[TYPE] in node_types_from_requirements:
                    self.add_template_dependency(node_name, req_node_name)

        # Search in all nodes for get function mentions and get its target name

        for node_name, node_tmpl in self.node_templates.items():
            self.search_get_function(node_name, node_tmpl)

        for rel_name, rel_tmpl in self.relationship_templates.items():
            self.search_get_function(rel_name, rel_tmpl)

    def search_get_function(self, node_name, data):
        """
        Function for recursion search of object in data
        Get functions are the keys of dictionary
        :param node_name:
        :param data:
        :return:
        """
        if isinstance(data, dict):
            for k, v in data.items():
                if k not in self.DEPENDENCY_FUNCTIONS:
                    self.search_get_function(node_name, v)
                else:
                    if isinstance(v, list):
                        template_name = v[0]
                    else:
                        params = v.split(',')
                        template_name = params[0]
                    if not template_name in TEMPLATE_REFERENCES:
                        self.add_template_dependency(node_name, template_name)
                        if self.relationship_templates.get(template_name) is not None and \
                                self._relation_target_source.get(template_name) is None:
                            self._relation_target_source[template_name] = {
                                'source': node_name,
                                'target': None
                            }
        elif isinstance(data, list):
            for i in data:
                self.search_get_function(node_name, i)
        elif isinstance(data, (str, int, float)):
            return

    def definition_file(self):
        file_definition = self.provider_config.config['main'][TOSCA_ELEMENTS_DEFINITION_FILE]
        if not os.path.isabs(file_definition):
            file_definition = os.path.join(self.provider_config.config_directory, file_definition)

        if not os.path.isfile(file_definition):
            logging.error("TOSCA definition file not found: %s" % file_definition)
            raise Exception("TOSCA definition file not found: %s" % file_definition)

        return file_definition

    def tosca_elements_map_to_provider(self):
        r = dict()
        for file in self.map_files:
            with open(file, 'r') as file_obj:
                data = file_obj.read()
                try:
                    data_dict = json.loads(data)
                    r.update(data_dict)
                except:
                    try:
                        data_dict = yaml.safe_load(data)
                        r.update(data_dict)
                    except yaml.scanner.ScannerError as e:
                        logging.error("Mapping file \'%s\' must be of type JSON or YAMl" % file)
                        logging.error("Error parsing TOSCA template: %s%s" % (e.problem, e.context_mark))
                        raise Exception("Error parsing TOSCA template: %s%s" % (e.problem, e.context_mark))
        return r

    def translate_to_provider(self):
        new_element_templates, new_extra, template_mapping = translate_to_provider(self)

        dict_tpl = {}
        self.template_mapping = template_mapping
        if new_element_templates.get(NODES):
            dict_tpl[NODE_TEMPLATES] = new_element_templates[NODES]
        if new_element_templates.get(RELATIONSHIPS):
            dict_tpl[RELATIONSHIP_TEMPLATES] = new_element_templates[RELATIONSHIPS]
        if new_element_templates.get(OUTPUTS):
            dict_tpl[OUTPUTS] = new_element_templates[OUTPUTS]
        if self.inputs:
            dict_tpl[INPUTS] = self.inputs

        rel_types = {}
        for k, v in self.definitions.items():
            (_, element_type, _) = utils.tosca_type_parse(k)
            if element_type == RELATIONSHIPS:
                rel_types[k] = v

        logging.debug("TOSCA template with non normative types for provider %s was generated: \n%s"
                      % (self.provider, yaml.dump(dict_tpl)))

        try:
            topology_tpl = TopologyTemplate(dict_tpl, self.definitions, rel_types=rel_types)
        except:
            logging.exception("Failed to parse intermidiate non-normative TOSCA template with OpenStack tosca-parser")
            raise Exception("Failed to parse intermidiate non-normative TOSCA template with OpenStack tosca-parser")

        self.extra_configuration_tool_params = utils.deep_update_dict(self.extra_configuration_tool_params, new_extra)

        self.node_templates = new_element_templates.get(NODES, {})
        self.relationship_templates = new_element_templates.get(RELATIONSHIPS, {})
        self.outputs = new_element_templates.get(OUTPUTS, {})

    def _get_property_value(self, value, tmpl_name):
        prop_keys = []
        tmpl_properties = None

        if value[0] == SELF:
            value[0] = tmpl_name
        if value[0] == HOST:
            value = [tmpl_name, 'host'] + value[1:]
        if value[0] in [SOURCE, TARGET]:
            # TODO
            logging.critical("Not implemented")
            raise Exception("Not implemented")
        node_tmpl = self.node_templates[value[0]]

        if node_tmpl.get(REQUIREMENTS, None) is not None:
            for req in node_tmpl[REQUIREMENTS]:
                if req.get(value[1], None) is not None:
                    if req[value[1]].get(NODE, None) is not None:
                        return self._get_property_value([req[value[1]][NODE]] + value[2:], req[value[1]][NODE])
                    if req[value[1]].get(NODE_FILTER, None) is not None:
                        tmpl_properties = {}
                        node_filter_props = req[value[1]][NODE_FILTER].get(PROPERTIES, [])
                        for prop in node_filter_props:
                            tmpl_properties.update(prop)
                        prop_keys = value[2:]
        if node_tmpl.get(CAPABILITIES, {}).get(value[1], None) is not None:
            tmpl_properties = node_tmpl[CAPABILITIES][value[1]].get(PROPERTIES, {})
            prop_keys = value[2:]
        if node_tmpl.get(PROPERTIES, {}).get(value[1], None) is not None:
            tmpl_properties = node_tmpl[PROPERTIES]
            prop_keys = value[1:]

        for key in prop_keys:
            if tmpl_properties.get(key, None) is None:
                tmpl_properties = None
                break
            tmpl_properties = tmpl_properties[key]
        if tmpl_properties is None:
            logging.error("Failed to get property: %s" % json.dumps(value))
            raise Exception("Failed to get property: %s" % json.dumps(value))
        return tmpl_properties

    def resolve_get_property_functions(self, data=None, tmpl_name=None):
        if data is None:
            data = self.node_templates
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if key == GET_PROPERTY:
                    new_data = self._get_property_value(value, tmpl_name)
                else:
                    new_data[key] = self.resolve_get_property_functions(value,
                                                                        tmpl_name if tmpl_name is not None else key)
            return new_data
        elif isinstance(data, list):
            new_data = []
            for v in data:
                new_data.append(self.resolve_get_property_functions(v, tmpl_name))
            return new_data
        elif isinstance(data, GetProperty):
            value = data.args
            return self._get_property_value(value, tmpl_name)
        return data

    def make_extended_notations(self):
        for tpl_name, tpl in self.node_templates.items():
            if tpl.get(REQUIREMENTS, None) is not None:
                for req in tpl[REQUIREMENTS]:
                    for req_name, req_body in req.items():
                        if isinstance(req_body, six.string_types):
                            req[req_name] = {
                                'node': req_body
                            }
            if tpl.get(ARTIFACTS, None) is not None:
                for art_name, art_body in tpl[ARTIFACTS].items():
                    if isinstance(art_body, six.string_types):
                        tpl[ARTIFACTS][art_name] = {
                            'file': art_body
                        }
            if tpl.get(INTERFACES, None) is not None:
                for inf_name, inf_body in tpl[INTERFACES].items():
                    for op_name, op_body in inf_body.items():
                        if op_name not in [DERIVED_FROM, TYPE, DESCRIPTION, INPUTS]:
                            if isinstance(op_body, six.string_types):
                                tpl[INTERFACES][inf_name][op_name] = {
                                    IMPLEMENTATION: {
                                        'primary': op_body,
                                        'dependencies': []
                                    },
                                    INPUTS: []
                                }
                            elif isinstance(op_body, list):
                                tpl[INTERFACES][inf_name][op_name] = {
                                    IMPLEMENTATION: {
                                        'primary': op_body[0] if len(op_body) >= 1 else [],
                                        'dependencies': op_body[1:] if len(op_body) >= 2 else []
                                    },
                                    INPUTS: []
                                }

    def _get_full_defintion(self, definition, def_type, ready_set):
        if def_type in ready_set:
            return definition, def_type in self.software_types

        (_, _, def_type_short) = utils.tosca_type_parse(def_type)
        is_software_type = def_type_short == 'SoftwareComponent'
        is_software_parent = False
        parent_def_name = definition.get(DERIVED_FROM, None)
        if parent_def_name is not None:
            if def_type == parent_def_name:
                logging.critical("Invalid type \'%s\' is derived from itself" % def_type)
                raise Exception("Invalid type \'%s\' is derived from itself" % def_type)
            if parent_def_name in ready_set:
                parent_definition = self.definitions[parent_def_name]
                is_software_parent = parent_def_name in self.software_types
            else:
                parent_definition, is_software_parent = \
                    self._get_full_defintion(self.definitions[parent_def_name], parent_def_name, ready_set)
            parent_definition = copy.deepcopy(parent_definition)
            definition = utils.deep_update_dict(parent_definition, definition)
        if is_software_type or is_software_parent:
            self.software_types.add(def_type)
        ready_set.add(def_type)
        return definition, def_type in self.software_types

    def fulfil_definitions_with_parents(self):
        ready_definitions = set()
        for def_name, definition in self.definitions.items():
            self.definitions[def_name], _ = self._get_full_defintion(definition, def_name, ready_definitions)
