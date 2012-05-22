from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import slugify
from mitel import esdblib
from django.shortcuts import render_to_response
from django.conf import settings
from generator import forms, models
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from gdata.sites import client as sites_client
import gdata.acl.data
import gdata.gauth
import gdata.sites
from gdata.data import MediaSource
from StringIO import StringIO

ESMITH_DB_DIRECTORY = None
if hasattr(settings, "DB_DIRECTORY"):
    ESMITH_DB_DIRECTORY = settings.DB_DIRECTORY

kwargs = {}
if ESMITH_DB_DIRECTORY:
    kwargs['dbdir'] = ESMITH_DB_DIRECTORY
    
def maybe_create_prop(record, name):
    prop = record.getProp(name)
    if not prop:
        prop = esdblib.EsmithDbProperty(name, '')
        record.addProp(prop, clobber=False, save=False)
    return prop

def maybe_create_record(db, name):
    record = db.getRecord(name)
    if not record:
        record = esdblib.EsmithDbRecord(db, key=name)
        db.addRecord(record, clobber=False, save=False)
    return record

gdb = esdblib.EsmithDb('googleapps', **kwargs)
    
xoauth = maybe_create_record(gdb, 'xoauth')
google = maybe_create_record(gdb, 'google')

admin_email = maybe_create_prop(google, 'admin_email')
site_id = maybe_create_prop(google, 'site_id')
key = maybe_create_prop(xoauth, 'consumer_key')
secret = maybe_create_prop(xoauth, 'consumer_secret')

def _create_page(client):
    entry = client.CreatePage('filecabinet', 'File Storage', html='<b>HTML content</b>', page_name='files')
    return entry

def _create_site(client, site_name):
    entry = client.CreateSite(site_name, page_name=slugify(site_name), description='Site to hold required Mitel integration files')
        
    scope = gdata.acl.data.AclScope(type='default')
    role = gdata.acl.data.AclRole(value='reader')
    acl = gdata.sites.data.AclEntry(scope=scope, role=role)
    
    try:
        _ = client.Post(acl, entry.FindAclLink())
    except:
        pass
    
    return entry
    
def _get_site(client, site):
    return client.GetEntry(site, desired_class=gdata.sites.data.SiteEntry)

def _get_installed():
    kwargs = {}
    if ESMITH_DB_DIRECTORY:
        kwargs['dbdir'] = ESMITH_DB_DIRECTORY
        
    class AppList(list):
        def __contains__(self, item):
            if type(item) is not str:
                return super(AppList, self).__contains__(item)
            
            for x in self:
                if x.key == item:
                    return True
                
            return False
        
    db = esdblib.EsmithDb('licensekeys', **kwargs)
    enabled = AppList(db.getAllByProp({
        'Status': 'enabled'
    }))
    
    return enabled

def main(request):
    auth_data = {
        'consumer_key': key.value,
        'consumer_secret': secret.value,
        'admin_email': admin_email.value,
    }
        
    if request.method == 'POST' and request.POST.get('submit_auth', False):
        auth_form = forms.GoogleConfigurationForm(request.POST)
        if auth_form.is_valid():
            key.value = auth_form.cleaned_data['consumer_key']
            secret.value = auth_form.cleaned_data['consumer_secret']
            admin_email.value = auth_form.cleaned_data['admin_email']
            
            apps_domain = admin_email.value.split('@')[-1]
            
            site_name = 'Mitel Integration'
            client = sites_client.SitesClient(source='mitel-v1', site=site_name, domain=apps_domain)
            client.auth_token = gdata.gauth.TwoLeggedOAuthHmacToken(
                key.value, secret.value, admin_email.value)
            
            if not site_id.value:
                entry = _create_site(client, site_name)
            else:
                entry = _get_site(client, site_id.value)
                
            site_id.value = entry.id.text
            
            client.site = entry.site_name.text
            
            try:        
                file_cabinet = _create_page(client)
                
                manifest_data = render_to_string('calendar_gadget.xml')
                file_length = len(manifest_data)
                manifest_file = StringIO(manifest_data)
                
                manifest = MediaSource(file_handle=manifest_file, 
                                       content_type='application/xml', 
                                       content_length=file_length,
                                       file_name='calendar_gadget.xml')
                _ = client.UploadAttachment(manifest, file_cabinet, content_type='application/xml',
                                                     title='calendar_gadget.xml', description='Integration Manifest')
            except:
                pass

            gdb.save()
            return HttpResponseRedirect(reverse('generator:home'))
    else:
        auth_form = forms.GoogleConfigurationForm(auth_data)
    
    licensed_apps = [{'status': x.getPropValue('Status'), 'key': x.key} for x in _get_installed()]
    ctx = {'licensed_apps': licensed_apps, 'auth_form': auth_form}
    
    ctx.update(csrf(request))
    return render_to_response('index.html', ctx)

def generate_manifest():
    licensed_apps = _get_installed()
    
    m = models.Manifest("Mitel Integration", "A simple application for testing contextual gadgets")
    
    if 'npm' in licensed_apps:
        mailScope = models.Scope(models.GoogleAPIs.IMAP_SMTP, 'This application needs access to your inbox.')
        subjectScope = models.Scope(models.ScopeURIs.SUBJECT, 'This application searches the Subject: line of each email for the text "Hello"')
        idScope = models.Scope(models.ScopeURIs.MESSAGE_ID, 'This application fetches the Message ID of the email.')
        fromScope = models.Scope(models.ScopeURIs.FROM_ADDRESS, 'This application fetches the Sender of the email.')
        
        contextual_gadget = models.ContextualGadget('http://s3.amazonaws.com/mitel-demo/gadget.xml', 'Hello World Gmail contextual gadget')  #Must be HTTP! WebSockets are broken otherwise
        contextual_gadget.add_scope(mailScope)
        
        subject_extractor = models.ContextExtractor('google.com:SubjectExtractor', 'Subject Extractor')
        subject_extractor.add_trigger(contextual_gadget)
        subject_extractor.add_param("subject", ".*Hello.*")
        subject_extractor.add_scope(subjectScope)
        
        id_extractor = models.ContextExtractor('google.com:MessageIDExtractor', 'ID Extractor')
        id_extractor.add_trigger(contextual_gadget)
        id_extractor.add_param("message_id", ".*")
        id_extractor.add_scope(idScope)
        
        from_extractor = models.ContextExtractor('google.com:SenderEmailExtractor', 'Sender Extractor')
        from_extractor.add_trigger(contextual_gadget)
        from_extractor.add_param("sender_email", ".*")
        from_extractor.add_scope(fromScope)
        
        m.add_extension(contextual_gadget)
        m.add_extension(subject_extractor)
        m.add_extension(id_extractor)
        m.add_extension(from_extractor)
        
    sitesScope = models.Scope(models.GoogleAPIs.SITES, 'This application needs access to your Google Sites.')
    calendar_gadget = models.ContextualGadget('https://s3.amazonaws.com/mitel-demo/gadget.xml', 'Calendar Gadget')
    calendar_gadget.add_scope(sitesScope)
    m.add_extension(calendar_gadget)
    
    return m

def manifest(request):
    m = generate_manifest()
    
    response = HttpResponse(m, mimetype="application/xhtml+xml")
    response['Content-Disposition'] = 'attachment; filename=%s' % 'Manifest.xml'
    return response
