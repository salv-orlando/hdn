# Copyright 2013 Somebody
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

from oslo_log import log
from sqlalchemy.orm import exc as sa_exc
from neutron.db import api as db_api
from neutron.db import db_base_plugin_v2
from neutron.db import external_net_db
from neutron.db import l3_db
from neutron.db import quota_db  # noqa

from hdn.common import config  # noqa
from hdn.common import constants
from hdn.common import hdnlib

LOG = log.getLogger(__name__)


class HdnNeutronPlugin(db_base_plugin_v2.NeutronDbPluginV2,
                       external_net_db.External_net_db_mixin):

    """Implement the Human-Defined-Networking plugin.

    Are you tired of all the hype and fuss about SDN?
    Does 'Network Virtualization' mean absolutely nothing to you?
    Are you afraid machines will take over the world and rule humans?

    Then this is your plugin. Automated network provisioning is for
    losers. Humans do it better.

    The HDN plugin relies on the knowledge and expertise of experienced
    IT departments which will be able to serve in the most efficient and
    personalized way all the networking requests that a tenant might
    express through the tenant API.

    Asynchronous request processing, eventual consistenty, queue
    prioritazion, and deadlock resolution are automatically provided by
    the HDN resolution.

    For enhanced security and reliability please employ at least 4 IT
    operators in order to be able to deal with 1 byzantine operator.

    """

    # This attribute specifies whether the plugin supports or not
    # bulk/pagination/sorting operations. Name mangling is used in
    # order to ensure it is qualified by class
    __native_bulk_support = True
    __native_pagination_support = True
    __native_sorting_support = True

    # This is just an educational plugin. Only the l3 extension is supported
    # In order to add an extension to a plugin, it is needed to:
    # 1 - Add the corresponding mixin to the plugin's base class list
    # 2 - Add the extension alias to the plugin's support_extension_aliases
    #     attribute
    supported_extension_aliases = ["external-net"]

    def create_network(self, context, network):
        """ Instruct HDN operators to create a network

        This function implements the "network create" Neutron API operation.

        @param context - The Neutron context reference. This parameter holds
        a database session (context.session), the identifier of the tenant
        performing the operation (context.tenant_id), and other attributes
        such as a flag to test whether the tenant is an administrator
        (context.is_admin)

        @param network - A dict containing data of the network to be created
        """

        # Set the status of the network as 'PENDING CREATE'
        network['network']['status'] = constants.STATUS_PENDING_CREATE
        with db_api.autonested_transaction(context.session):
            new_net = super(HdnNeutronPlugin, self).create_network(
                context, network)

        # Use the HDN library to notify operators about the new network
        LOG.debug("Queued request to create network: %s", new_net['id'])
        hdnlib.notify_network_create(new_net)
        return new_net

    # the update network operation is merely a db operation.
    # The HDN plugin therefore does not override it.

    def delete_network(self, context, network_id, hdn_operator_call=False):
        with db_api.autonested_transaction(context.session):
            if hdn_operator_call:
                # the network must be removed from the DB
                super(HdnNeutronPlugin, self).delete_network(context,
                                                             network_id)
                LOG.debug("Network delete operation for %s completed",
                          network_id)
                return
            # _get_network returns a sqlalchemy model
            network = self._get_network(context, network_id)
            # Set the status of the network as 'PENDING DELETE'
            network.status = constants.STATUS_PENDING_DELETE

        hdnlib.notify_network_delete({'id': network_id,
                                      'tenant_id': context.tenant_id})
        LOG.debug("Queued request to delete network: %s", network_id)

    # GET operations for networks are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin

    def create_port(self, context, port):
        # Set port status as PENDING_CREATE
        port['port']['status'] = constants.STATUS_PENDING_CREATE
        with db_api.autonested_transaction(context.session):
            new_port = super(HdnNeutronPlugin, self).create_port(
                context, port)
        # Notify HDN operators
        hdnlib.notify_port_create(new_port)
        LOG.debug("Queued request to create port: %s", new_port['id'])
        return new_port

    def update_port(self, context, port_id, port):
        with db_api.autonested_transaction(context.session):
            original_port = super(HdnNeutronPlugin, self).get_port(
                context, port_id)
            updated_port = super(HdnNeutronPlugin, self).update_port(
                context, port_id, port)

        # TODO(salv-orlando): check for more attribute changes
        if original_port['admin_state_up'] != updated_port['admin_state_up']:
            # Put the port in PENDING_UPDATE status
            # Notify HDN operators
            with context.session.begin(subtransactions=True):
                db_port = self._get_port(context, port_id)
                db_port.status = constants.STATUS_PENDING_UPDATE
            hdnlib.notify_port_update(self._make_port_dict(db_port))
            LOG.debug("Queued request to update port: %s", port['id'])
        return updated_port

    def delete_port(self, context, port_id, hdn_operator_call=False):
        # if needed, check to see if this is a port owned by
        # a l3-router.  If so, we should prevent deletion.
        # Therefore notify registry so that pre-delete checks can be run
        with context.session.begin(subtransactions=True):
            # _get_port returns a sqlalchemy model
            port = self._get_port(context, port_id)
            if hdn_operator_call:
                # the port must be removed from the DB
                super(HdnNeutronPlugin, self).delete_port(context, port_id)
                LOG.debug("Port delete operation for %s completed",
                          port_id)
                return
            # Put the port in PENDING_DELETE constants.STATUS
            port.status = constants.STATUS_PENDING_DELETE
            # TODO(salv-orlando): Notify callback to disassociate floating IPs
            # on l3 service plugin
        # Notify HDN operators
        hdnlib.notify_port_delete({'id': port_id,
                                   'tenant_id': context.tenant_id})
        LOG.debug(_("Queued request to delete port: %s"), port_id)

    # GET operations for ports are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin

    def create_subnet(self, context, subnet):
        subnet['subnet']['status'] = constants.STATUS_PENDING_CREATE
        new_subnet = super(HdnNeutronPlugin, self).create_subnet(
            context, subnet)
        # Notify HDN operators
        hdnlib.notify_subnet_create(new_subnet)
        LOG.debug("Queued request to create subnet: %s", new_subnet['id'])
        return new_subnet

    def update_subnet(self, context, subnet_id, subnet):
        # Put the subnet in PENDING UPDATE status
        subnet['subnet']['status'] = constants.STATUS_PENDING_UPDATE
        upd_subnet = super(HdnNeutronPlugin, self).update_subnet(
            context, subnet_id, subnet)
        LOG.debug("Queued request to update subnet: %s", subnet['id'])
        # Notify HDN operators
        hdnlib.notify_subnet_update(upd_subnet)
        return upd_subnet

    def delete_subnet(self, context, subnet_idi, hdn_operator_call=False):
        # Put the subnet in PENDING_DELETE status
        with db_api.autonested_transaction(context.session):
            # _get_subnet returns a sqlalchemy model
            subnet = self._get_subnet(context, subnet_id)
            if hdn_operator_call:
                # the subnet must be removed from the DB
                super(HdnNeutronPlugin, self).delete_subnet(context,
                                                            subnet_id)
                return
            subnet.status = constants.STATUS_PENDING_DELETE
        # Notify HDN operators
        hdnlib.notify_subnet_delete({'id': subnet_id,
                                     'tenant_id': context.tenant_id})
        LOG.debug("Queued request to delete subnet: %s", subnet_id)
