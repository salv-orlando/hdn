#!/bin/bash

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

# devstack/plugin.sh
# Functions to control the configuration and operation of the HDN service

# Dependencies:
#
# ``functions`` file
# ``DEST`` must be defined
# ``STACK_USER`` must be defined

# ``stack.sh`` calls the entry points in this order:
#
# - install_hdn
# - configure_hdn
# - configure_hdn_plugin
# - init_hdn
# - start_hdn
# - stop_hdn
# - cleanup_hdn

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace


HDN_DIR=$DEST/hdn


function neutron_plugin_setup_interface_driver {
    :
}


function neutron_plugin_configure_debug_command {
    :
}


function neutron_plugin_create_nova_conf {
    :
}


# OVS is evil
function is_neutron_ovs_base_plugin {
    return 0
}


function configure_hdn_plugin {
    echo "Configuring Neutron for enabling HDN"

    # Tempest uses this variable for determining which tests should be run
    export NETWORK_API_EXTENSIONS='quotas,external-net,router,security-group'
    iniset $NEUTRON_CONF DEFAULT core_plugin "$Q_PLUGIN_CLASS"
    iniset $NEUTRON_CONF DEFAULT service_plugins  "$Q_SERVICE_PLUGIN_CLASSES"
}


if [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_hdn_plugin
    if is_service_enabled nova; then
        create_nova_conf_neutron
    fi
fi

# Restore xtrace
$XTRACE

