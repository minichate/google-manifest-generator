from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns('',
    url(r'^', include('generator.urls', namespace='generator', app_name='generator')),
)
