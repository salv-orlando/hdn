# vim: tabstop=4 shiftwidth=4 softtabstop=4
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
from neutron.db import db_base_plugin_v2
from neutron.db import external_net_db
from neutron.db import l3_db
from neutron.db import quota_db  # noqa
from neutron.extensions import l3

from hdn.common import config  # noqa
from hdn.common import hdnlib

LOG = log.getLogger(__name__)
STATUS_PENDING_CREATE = 'PENDING_CREATE'
STATUS_PENDING_UPDATE = 'PENDING_UPDATE'
STATUS_PENDING_DELETE = 'PENDING_DELETE'


class HdnNeutronPlugin(db_base_plugin_v2.NeutronDbPluginV2,
                       external_net_db.External_net_db_mixin,
                       l3_db.L3_NAT_db_mixin):

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
    supported_extension_aliases = ["external-net", "router"]

    def __init__(self, configfile=None):
        # TODO(salv-orlando): Validate configuration
        pass

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
        network['network']['status'] = STATUS_PENDING_CREATE
        with context.session.begin(subtransactions=True):
            new_net = super(HdnNeutronPlugin, self).create_network(
                context, network)
        # Use the HDN library to notify operators about the new network

        LOG.debug(_("Queued request to create network: %s"), new_net['id'])
        hdnlib.notify_network_create(new_net)
        return new_net

    def update_network(self, context, network_id, network):
        # the update network operation is merely a db operation.
        # No HDN request needs to be sent
        with context.session.begin(subtransactions=True):
            net = super(HdnNeutronPlugin, self).update_network(
                context, network_id, network)
        return net

    def delete_network(self, context, network_id):
        with context.session.begin(subtransactions=True):
            # _get_network returns a sqlalchemy model
            network = self._get_network(context, network_id)
            if context.is_admin and network.status == STATUS_PENDING_DELETE:
                # the network must be removed from the DB
                super(HdnNeutronPlugin, self).delete_network(context,
                                                             network_id)
                return
            # Set the status of the network as 'PENDING DELETE'
            network.status = STATUS_PENDING_DELETE

        hdnlib.notify_network_delete({'id': network_id,
                                      'tenant_id': context.tenant_id})
        LOG.debug(_("Queued request to delete network: %s"), network_id)

    # GET operations for networks are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin

    def create_port(self, context, port):
        # Set port status as PENDING_CREATE
        port['port']['status'] = STATUS_PENDING_CREATE
        with context.session.begin(subtransactions=True):
            new_port = super(HdnNeutronPlugin, self).create_port(
                context, port)
        # Notify HDN operators
        hdnlib.notify_port_create(new_port)
        LOG.debug(_("Queued request to create port: %s"), new_port['id'])
        return new_port

    def update_port(self, context, port_id, port):
        with context.session.begin(subtransactions=True):
            original_port = super(HdnNeutronPlugin, self).get_port(
                context, port_id)
            updated_port = super(HdnNeutronPlugin, self).update_port(
                context, port_id, port)

        if original_port['admin_state_up'] != updated_port['admin_state_up']:
            # Put the port in PENDING_UPDATE status
            # Notify HDN operators
            with context.session.begin(subtransactions=True):
                db_port = self._get_port(context, port_id)
                db_port.status = STATUS_PENDING_UPDATE
            hdnlib.notify_port_update(self._make_port_dict(db_port))
            LOG.debug(_("Queued request to update port: %s"), port['id'])
        return updated_port

    def delete_port(self, context, port_id, l3_port_check=True):
        # if needed, check to see if this is a port owned by
        # and l3-router.  If so, we should prevent deletion.
        if l3_port_check:
            self.prevent_l3_port_deletion(context, port_id)
        with context.session.begin(subtransactions=True):
            # _get_port returns a sqlalchemy model
            port = self._get_port(context, port_id)
            if context.is_admin and port.status == STATUS_PENDING_DELETE:
                # the port must be removed from the DB
                super(HdnNeutronPlugin, self).delete_port(context, port_id)
                return
            # This is needed by L3 extension
            self.disassociate_floatingips(context, port_id)
            # Put the port in PENDING_DELETE STATUS
            port.status = STATUS_PENDING_DELETE
        # Notify HDN operators
        hdnlib.notify_port_delete({'id': port_id,
                                   'tenant_id': context.tenant_id})
        LOG.debug(_("Queued request to delete port: %s"), port_id)

    # GET operations for ports are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin

    def create_subnet(self, context, subnet):
        subnet['subnet']['status'] = STATUS_PENDING_CREATE
        new_subnet = super(HdnNeutronPlugin, self).create_subnet(
            context, subnet)
        # Notify HDN operators
        hdnlib.notify_subnet_create(new_subnet)
        LOG.debug(_("Queued request to create subnet: %s"), new_subnet['id'])
        return new_subnet

    def update_subnet(self, context, subnet_id, subnet):
        # Put the subnet in PENDING UPDATE status
        subnet['subnet']['status'] = STATUS_PENDING_UPDATE
        upd_subnet = super(HdnNeutronPlugin, self).update_subnet(
            context, subnet_id, subnet)
        LOG.debug(_("Queued request to update subnet: %s"), subnet['id'])
        # Notify HDN operators
        hdnlib.notify_subnet_update(upd_subnet)
        return upd_subnet

    def delete_subnet(self, context, subnet_id):
        # Put the subnet in PENDING_DELETE status
        with context.session.begin(subtransactions=True):
            # _get_subnet returns a sqlalchemy model
            subnet = self._get_subnet(context, subnet_id)
            if context.is_admin and subnet.status == STATUS_PENDING_DELETE:
                # the subnet must be removed from the DB
                super(HdnNeutronPlugin, self).delete_subnet(context,
                                                            subnet_id)
                return
            subnet.status = STATUS_PENDING_DELETE
        # Notify HDN operators
        hdnlib.notify_subnet_delete({'id': subnet_id,
                                     'tenant_id': context.tenant_id})
        LOG.debug(_("Queued request to delete subnet: %s"), subnet_id)

    # GET operations for subnets are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin

    # ******************************************
    # Neutron L3 extension implementation
    # *****************************************

    def prevent_l3_port_deletion(self, context, port_id):
        """Overriden from base class

        This version of this method allows HDN admin operators
        to remove service ports using the Neutron API.
        """
        if not context.is_admin:
            super(HdnNeutronPlugin, self).prevent_l3_port_deletetion(
                self, context, port_id)

    def create_router(self, context, router):
        # Put the router in PENDING CREATE
        router['router']['status'] = STATUS_PENDING_CREATE
        new_router = super(HdnNeutronPlugin, self).create_router(
            context, router)
        # Notify HDN operators
        hdnlib.notify_router_create(new_router)
        LOG.debug(_("Queued request to create router: %s"), new_router['id'])
        return new_router

    def update_router(self, context, router_id, router):
        # Put the router in PENDING_UPDATE
        router['router']['status'] = STATUS_PENDING_UPDATE
        upd_router = super(HdnNeutronPlugin, self).update_router(
            context, router)
        # Notify HDN operators
        hdnlib.notify_router_update(upd_router)
        LOG.debug(_("Queued request to update router: %s"), router['id'])
        return upd_router

    def delete_router(self, context, router_id, router):
        # Pre-delete checks
        # Ensure that the router is not used
        fips = self.get_floatingips_count(
            context.elevated(), filters={'router_id': [router_id]})
        if fips:
            raise l3.RouterInUse(router_id=router_id)

        device_filter = {'device_id': [router_id],
                         'device_owner': [l3_db.DEVICE_OWNER_ROUTER_INTF]}
        ports = self._core_plugin.get_ports_count(context.elevated(),
                                                  filters=device_filter)
        if ports:
            raise l3.RouterInUse(router_id=router_id)
        # Put the router in PENDING_DELETE status
        with context.session.begin(subtransactions=True):
            router = self._get_router(context, router_id)
            router.status = STATUS_PENDING_DELETE
        # Notify HDN operators
        hdnlib.notify_router_delete({'id': router_id,
                                     'tenant_id': context.tenant_id})
        LOG.debug(_("Queued request to delete router: %s"), router_id)

    # GET operations for routers are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin

    def _update_fip_assoc(self, context, fip, floatingip_db, external_port):
        """Performs association of a floating IP with a port.

        This method is invoked by create_floatingip and update_floatingip.
        """
        super(HdnNeutronPlugin, self).update_fip_assoc(
            context, fip, floatingip_db, external_port)
        # Notify HDN operators
        hdnlib.notify_floatingip_update_association(floatingip_db)
        # TODO(salv): Add operational status for floating IPs

    def delete_floatingip(self, context, floatingip_id):
        # TODO(salv): Add operational status for floating IPs
        # Notify HDN operators
        hdnlib.notify_floatingip_delete({'id': floatingip_id,
                                         'tenant_id': context.tenant_id})
        LOG.debug(_("Queued request to delete floating ip: %s"),
                  floatingip_id)

    def disassociate_floatingips(self, context, port_id):
        # This method is redefined as this plugin does not use a RPC
        # notifier, which would be against the HDN principles.
        with context.session.begin(subtransactions=True):
            try:
                fip_qry = context.session.query(l3_db.FloatingIP)
                floating_ip = fip_qry.filter_by(fixed_port_id=port_id).one()
                floating_ip.update({'fixed_port_id': None,
                                    'fixed_ip_address': None,
                                    'router_id': None})
                # Notify HDN operators for each floating IP
                hdnlib.notify_floatingip_disassociate(floating_ip)
            except sa_exc.NoResultFound:
                return
            except sa_exc.MultipleResultsFound:
                # should never happen
                raise Exception(_('Multiple floating IPs found for port %s'))

    # GET operations for floating IPs are not redefined. The operation defined
    # in NeutronDBPluginV2 is enough for the HDN plugin
