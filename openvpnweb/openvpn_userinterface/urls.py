# vim: shiftwidth=4 expandtab

from django.conf.urls.defaults import *
from openvpnweb.openvpn_userinterface.views import *

urlpatterns = patterns('',

#URLs for  user interface
    url(r'^$', main_page, name="main_page"),
    url(r'^login/$', login_page, name="login_page"),
#    url(r'^revoke/$', revoke_page, name="revoke_page"),
    url(r'^revoke/(?P<cert_id>\d+)$', revoke_page, name="revoke_page"),
    url(r'^order/(?P<org_id>\d+)/(?P<network_id>\d+)$', order_page,
        name="order_page"),
    url(r'^logout/$', logout_page, name="logout_page"),
    url(r'^manage/$', manage_page, name="manage_page"),
    url(r'^manage/org/(?P<org_id>\d+)$', manage_org_page,
        name="manage_org_page"),
)
