from jinja2 import Environment, PackageLoader
import google_manifest_generator as manifest

env = Environment(loader=PackageLoader('google_manifest_generator', 'templates'))

if __name__ == '__main__':
    template = env.get_template('manifest.xml')
    manifest_file = manifest.Manifest("Mitel Gadget", "Test")
    
    g1 = manifest.ContextualGadget("http://test/gadget.xml", "Test")
    g1.add_scope(manifest.Scope("http://google.com", "For fun"))
    manifest_file.add_extension(g1)
    
    extractorScope1 = manifest.Scope("tag:google.com,2010:auth/contextual/extractor/SUBJECT", "This application searches the Subject")
    
    c1 = manifest.ContextExtractor("google.com:SenderEmailExtractor", "Email Sender")
    c1.add_scope(extractorScope1)
    c1.add_trigger(g1)
    c1.add_param("message_id", ".*")
    manifest_file.add_extension(c1)
    
    manifest_file.add_support(manifest.Support(manifest.LinkRel.SUPPORT, "http://google.com"))
    manifest_file.add_support(manifest.Support(manifest.LinkRel.MANAGE, "http://google.com"))
    
    manifest_file.add_scope(manifest.Scope("http://other/", "Wewt"))
    
    manifest_file.add_extension(manifest.OpenIdRealm("http://app.gtraxapp.com"))
    manifest_file.add_extension(manifest.Link("http://app.gtraxapp.com"))
    
    print template.render(manifest=manifest_file)
