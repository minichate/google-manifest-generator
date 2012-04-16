from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'generator.views.main', name='home'),
    url(r'^manifest.xml$', 'generator.views.manifest', name='manifest'),
)
