# Copyright 2015 MeH
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc
from neutron.api import extensions
from neutron.api.v2 import attributes
from neutron.api.v2 import resource_helper

from hdn.common import constants
from hdn import extensions as hdn_extensions

# Ensure the extension is loaded at startup
extensions.append_api_extensions_path(hdn_extensions.__path__)


RESOURCE_ATTRIBUTE_MAP = {
    'tasks': {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'action': {'allow_post': False, 'allow_put': False,
                   'validate': {'type:string': None},
                   'is_visible': True, 'default': ''},
        'object': {'allow_post': False, 'allow_put': False,
                   'is_visible': True},
        'type': {'allow_post': False, 'allow_put': True,
                 'is_visible': True},
        'tenant_id': {'allow_post': False, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True,
                      'is_visible': True},
        'status': {'allow_post': False, 'allow_put': False,
                   'validate': {'type:string': None},
                   'required_by_policy': True,
                   'is_visible': True}
    }
}


class Hdntasks(extensions.ExtensionDescriptor):

    """API extension for handling HDN tasks."""

    @classmethod
    def get_name(cls):
        return "HDN tasks"

    @classmethod
    def get_alias(cls):
        return "hdn-tasks"

    @classmethod
    def get_description(cls):
        return "Provides a REST API for HDN operators to manage their tasks."

    @classmethod
    def get_updated(cls):
        return "2015-10-01T00:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        attributes.PLURALS.update(plural_mappings)
        resources = resource_helper.build_resource_info(plural_mappings,
                                                        RESOURCE_ATTRIBUTE_MAP,
                                                        constants.HDN_TASKS)

        return resources

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


class HdnTaskPluginBase(object):

    @abc.abstractmethod
    def get_tasks(self, context, filters=None, fields=None,
                  sorts=None, limit=None, marker=None,
                  page_reverse=False):
        pass

    @abc.abstractmethod
    def get_task(self, context, task_id, fields=None):
        pass

    @abc.abstractmethod
    def create_task(self, context, task_info):
        pass

    @abc.abstractmethod
    def delete_task(self, context, task_id):
        pass

    @abc.abstractmethod
    def update_task(self, context, task_id, task_info):
        pass
