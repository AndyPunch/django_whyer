from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from views import search_view, contact_view

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^about_us/$',
                           TemplateView.as_view(template_name='about_us.html'),
                           name='about_us'),
                       url(r'^contact/$', contact_view, name='contact'),
                       url(r'^search/$', search_view, name='search'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^', include('questions_answers.urls')),
                       url(r'^profile/', include('profiles.urls')),
                       url(r"^accounts/", include('allauth.urls')),
                       url(r'^summernote/', include('django_summernote.urls')),
                       )

if settings.DEBUG:
    if settings.MEDIA_ROOT:
        urlpatterns += static(settings.MEDIA_URL,
                              document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()


