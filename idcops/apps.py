# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig


class IdcopsConfig(AppConfig):
    name = 'idcops'
    verbose_name = u"数据中心运维"

    def ready(self):
        from idcops.lib import signals
