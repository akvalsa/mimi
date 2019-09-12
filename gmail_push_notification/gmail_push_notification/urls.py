from django.conf.urls import include, url
from django.contrib import admin

from push_to_ftp.views import process_gmail

urlpatterns = [
    # Examples:
    # url(r'^$', 'gmail_push_notification.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/process_gmail/', process_gmail),
]
