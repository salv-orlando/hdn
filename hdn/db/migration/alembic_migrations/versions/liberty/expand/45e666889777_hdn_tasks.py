# Copyright 2015 OpenStack Foundation
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
#

"""hdn_tasks

Revision ID: 45e666889777
Revises: liberty_exp
Create Date: 2015-10-01
"""

# revision identifiers, used by Alembic.
revision = '45e666889777'
down_revision = 'liberty_exp'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    op.create_table(
        'hdntasks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('object_id', sa.String(length=36), nullable=False),
        sa.Column('object_type', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=16)),
        sa.Column('status_description', sa.String(length=255)))
