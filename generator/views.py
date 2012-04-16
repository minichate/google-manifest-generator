from django.http import HttpResponse
from mitel import esdblib
import models
from django.shortcuts import render_to_response
from django.conf import settings

def _get_installed():
    kwargs = {}
    if hasattr(settings, "DB_DIRECTORY"):
        kwargs['dbdir'] = settings.DB_DIRECTORY
        
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
    licensed_apps = [{'status': x.getPropValue('Status'), 'key': x.key} for x in _get_installed()]
    return render_to_response('index.html', {'licensed_apps': licensed_apps})

def manifest(request):
    licensed_apps = _get_installed()
    
    m = models.Manifest("Mitel Gadget", "A simple application for testing contextual gadgets")
    
    if 'npm' in licensed_apps:
        mailScope = models.Scope(models.GoogleAPIs.IMAP_SMTP, 'This application needs access to your inbox.')
        subjectScope = models.Scope(models.ScopeURIs.SUBJECT, 'This application searches the Subject: line of each email for the text "Hello"')
        idScope = models.Scope(models.ScopeURIs.MESSAGE_ID, 'This application fetches the Message ID of the email.')
        
        gadget = models.ContextualGadget('https://s3.amazonaws.com/mitel-demo/gadget.xml', 'Hello World Gmail contextual gadget')
        gadget.add_scope(mailScope)
        
        subject_extractor = models.ContextExtractor('google.com:SubjectExtractor', 'Subject Extractor')
        subject_extractor.add_trigger(gadget)
        subject_extractor.add_param("subject", ".*Hello.*")
        subject_extractor.add_scope(subjectScope)
        
        id_extractor = models.ContextExtractor('google.com:MessageIDExtractor', 'ID Extractor')
        id_extractor.add_trigger(gadget)
        id_extractor.add_param("message_id", ".*")
        id_extractor.add_scope(idScope)
        
        m.add_extension(gadget)
        m.add_extension(subject_extractor)
        m.add_extension(id_extractor)
    
    response = HttpResponse(m, mimetype="application/xhtml+xml")
    #response['Content-Disposition'] = 'attachment; filename=%s' % 'Manifest.xml'
    return response