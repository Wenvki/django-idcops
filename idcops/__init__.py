from django.db.models.options import Options
from django.db.models import options
from django.db import models

default_app_config = 'idcops.apps.IdcopsConfig'

__version__ = '1.0.2'

EXT_NAMES = (
    'level', 'hidden', 'dashboard', 'metric', 'icon',
    'icon_color', 'default_filters',
    'list_display', 'extra_fields'
)

options.DEFAULT_NAMES += EXT_NAMES


def monkey_options_init(self, meta, app_label):
    self._old__init__(meta, app_label)
    self.default_permissions = ('view', 'add', 'change', 'delete', 'export')


# TODO: create PR to Django - default_permissions from settings
Options._old__init__ = Options.__init__
Options.__init__ = lambda self, meta, app_label=None: monkey_options_init(
    self, meta, app_label
)
