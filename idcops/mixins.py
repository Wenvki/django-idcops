# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.apps import apps
from django.core.cache import cache, utils
from django.core.urlresolvers import reverse_lazy
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.utils.encoding import force_text
from django.views.generic.base import logger

# Create your views here.
from idcops.lib.utils import get_query_string, get_content_type_for_model
from idcops.models import Configure, Idc


def construct_menus():
    model_names = []
    for app in apps.get_app_config('idcops').get_models():
        opts = app._meta
        if not getattr(opts, 'hidden', False):
            meta = {
                'model_name': opts.model_name,
                'verbose_name': opts.verbose_name,
                'icon': opts.icon,
                'icon_color': 'text-' + opts.icon_color,
                'level': opts.level,
            }
            model_names.append(meta)
    counts = list(set([i.get('level') for i in model_names]))
    new_menus = []
    for i in counts:
        new_menus.append(
            [c for c in model_names if c.get('level') == i]
        )
    return new_menus


system_menus_key = utils.make_template_fragment_key('system.menus')
system_menus = cache.get_or_set(system_menus_key, construct_menus(), 360)


def get_user_config(user, mark, model):
    content_type = get_content_type_for_model(model)
    configs = Configure.objects.filter(
        creator=user,
        mark=mark,
        content_type=content_type).order_by('-pk')
    if configs.exists():
        config = configs.first().content
        try:
            return json.loads(config)
        except BaseException:
            return None
    else:
        return None


class BaseRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "需登录系统才能访问")
            return redirect_to_login(
                request.get_full_path(),
                self.get_login_url(), self.get_redirect_field_name())
        if not request.user.onidc:
            idc = Idc.objects.filter(actived=True)
            if idc.count() == 0 and request.user.is_superuser:
                messages.warning(
                    request,
                    "您必须指定一个所属机房, 请新建一个机房并将用户关联至此机房")
                return HttpResponseRedirect('/admin/idcops/idc/add/')
            else:
                messages.warning(
                    request,
                    "您必须指定一个所属机房, 请选择用户所属机房字段内容"
                )
                return HttpResponseRedirect(
                    '/admin/idcops/user/{}/change/'.format(request.user.pk))
            return self.handle_no_permission()
        model = self.kwargs.get('model', None)
        onidc = request.user.onidc
        self.onidc_id = onidc.id
        self.title = "{} 数据中心运维平台".format(onidc.name)
        if model:
            try:
                self.model = apps.get_model('idcops', model.lower())
                self.opts = self.model._meta
                self.model_name = self.opts.model_name
                self.verbose_name = self.opts.verbose_name
                if self.kwargs.get('pk', None):
                    self.pk_url_kwarg = self.kwargs.get('pk')
            except BaseException:
                raise Http404("您访问的模块不存在.")
        return super(BaseRequiredMixin, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BaseRequiredMixin, self).get_context_data(**kwargs)
        self.meta = {}
        try:
            self.meta['logo'] = self.request.user.onidc.name
            self.meta['icon'] = self.opts.icon
            self.meta['model_name'] = self.model_name
            self.meta['verbose_name'] = self.verbose_name
            self.meta['title'] = "{} {}".format(self.verbose_name, self.title)
        except BaseException:
            self.meta['title'] = self.title
        context['meta'] = self.meta
        context['menus'] = system_menus
        from django import db
        logger.info('queries count: {}'.format(len(db.connection.queries)))
        return context


class PostRedirect(object):

    def get_success_url(self):
        if '_addanother' in self.request.POST:
            url = reverse_lazy('idcops:new', kwargs={'model': self.model_name})
            params = get_query_string(self.request.GET.copy())
            success_url = force_text(url + params)
        elif '_saverview' in self.request.POST:
            kwargs = {'model': self.model_name, 'pk': self.object.pk}
            success_url = reverse_lazy('idcops:detail', kwargs=kwargs)
        elif '_last' in self.request.POST:
            referrer = self.request.META.get('HTTP_REFERER', None)
            success_url = referrer
        else:
            kwargs = {'model': self.model_name}
            success_url = reverse_lazy('idcops:list', kwargs=kwargs)
        return success_url
