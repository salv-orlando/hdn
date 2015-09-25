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
#    under the License

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import itertools
import smtplib

from oslo.config import cfg


def send_mail(subject, text):
    msg = MIMEMultipart()
    msg['From'] = cfg.CONF.HDN.smtp_user
    msg['To'] = ",".join(cfg.CONF.HDN.recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    mailServer = smtplib.SMTP(cfg.CONF.HDN.smtp_server,
                              cfg.CONF.HDN.smtp_port)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(cfg.CONF.HDN.smtp_user,
                     cfg.CONF.HDN.smtp_password)
    mailServer.sendmail(cfg.CONF.HDN.smtp_user,
                        cfg.CONF.HDN.recipients,
                        msg.as_string())
    mailServer.close()


def _prepare_message(data):

    def _build_line(key, value):
        return "%s: %s\n" % (key, value)

    message_lines = itertools.imap(_build_line,
                                   data.keys(),
                                   data.values())
    return "".join(message_lines)


def notify_network_create(network_data):
    subject = "[HDN] Create network request:%s" % network_data['id']
    send_mail(subject, _prepare_message(network_data))


def notify_network_delete(network_data):
    subject = "[HDN] Delete network request:%s" % network_data['id']
    message = "Request coming from tenant:%s" % network_data['tenant_id']
    send_mail(subject, message)


def notify_port_create(port_data):
    subject = "[HDN] Create port request:%s" % port_data['id']
    send_mail(subject, _prepare_message(port_data))


def notify_port_update(port_data):
    subject = "[HDN] Update port request:%s" % port_data['id']
    send_mail(subject, _prepare_message(port_data))


def notify_port_delete(port_data):
    subject = "[HDN] Delete port request:%s" % port_data['id']
    message = "Request coming from tenant:%s" % port_data['tenant_id']
    send_mail(subject, message)


def notify_subnet_create(subnet_data):
    subject = "[HDN] Create subnet request:%s" % subnet_data['id']
    send_mail(subject, _prepare_message(subnet_data))


def notify_subnet_update(subnet_data):
    subject = "[HDN] Update subnet request:%s" % subnet_data['id']
    send_mail(subject, _prepare_message(subnet_data))


def notify_subnet_delete(subnet_data):
    subject = "[HDN] Delete subnet request:%s" % subnet_data['id']
    message = "Request coming from tenant:%s" % subnet_data['tenant_id']
    send_mail(subject, message)


def notify_router_create(router_data):
    subject = "[HDN] Create router request:%s" % router_data['id']
    send_mail(subject, _prepare_message(router_data))


def notify_router_update(router_data):
    subject = "[HDN] Update router request:%s" % router_data['id']
    send_mail(subject, _prepare_message(router_data))


def notify_router_delete(router_data):
    subject = "[HDN] Delete router request:%s" % router_data['id']
    message = "Request coming from tenant:%s" % router_data['tenant_id']
    send_mail(subject, message)


def notify_floatingip_update_association(floatingip_data):
    subject = ("[HDN] Floating IP association updated for:%s" %
               floatingip_data['id'])
    send_mail(subject, _prepare_message(floatingip_data))


def notify_floatingip_disassociate(floatingip_data):
    subject = ("[HDN] Floating IP disassociated:%s" %
               floatingip_data['id'])
    send_mail(subject, _prepare_message(floatingip_data))


def notify_floatingip_delete(floatingip_data):
    subject = "[HDN] Delete floating ip request:%s" % floatingip_data['id']
    message = "Request coming from tenant:%s" % floatingip_data['tenant_id']
    send_mail(subject, message)
