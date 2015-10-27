# Copyright 2015 Taturiello Consulting
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

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron import context
from neutron.db import common_db_mixin
from neutron.services import service_base

from oslo_log import log

from hdn.common import constants
from hdn.extensions import hdntasks

LOG = log.getLogger(__name__)


class HdnTasksPlugin(service_base.ServicePluginBase,
                     hdntasks.HdnTaskPluginBase,
                     common_db_mixin.CommonDbMixin):

    supported_extension_aliases = ["hdn-tasks"]

    def _build_task_info(self, tenant_id, resource_id,
                         object_type, action):
        return {'tenant_id': tenant_id,
                'resource_id': resource_id,
                'object_type': object_type,
                'action': action}

    def _add_network_create_task(self, tenant_id, resource_id):
        task_info = self._build_task_info(
            tenant_id, resource_id,
            'network', 'create')
        self.create_task(
            context.get_admin_context(), task_info)

    def _add_port_create_task(self, tenant_id, resource_id):
        task_info = self._build_task_info(
            tenant_id, resource_id,
            'network', 'create')
        self.create_task(
            context.get_admin_context(), task_info)

    def _add_router_create_task(self, tenant_id, resource_id):
        task_info = self._build_task_info(
            tenant_id, resource_id,
            'network', 'create')
        self.create_task(
            context.get_admin_context(), task_info)

    registry.subscribe(_add_network_create_task,
                       'NETWORK',
                       events.AFTER_CREATE)
    registry.subscribe(_add_port_create_task,
                       resources.PORT,
                       events.AFTER_CREATE)
    registry.subscribe(_add_router_create_task,
                       resources.ROUTER,
                       events.AFTER_CREATE)

    def get_plugin_type(self):
        # Tell Neutron this is a L3 service plugin
        return constants.HDN_TASK

    def get_plugin_description(self):
        return "HDN - support for task management"

    def get_tasks(self, context, filters=None, fields=None,
                  sorts=None, limit=None, marker=None,
                  page_reverse=False):
        LOG.debug("List tasks stub")
        return []

    def get_task(self, context, task_id, fields=None):
        LOG.debug("Get task stub")
        return {}

    def create_task(self, context, task_info):
        LOG.debug("Create task stub")

    def delete_task(self, context, task_id):
        LOG.debug("Delete task stub")

    def update_task(self, context, task_id, task_info):
        LOG.debug("Update task stub")
