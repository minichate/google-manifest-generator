# -*- coding: utf-8 -*-
import random, string

def _uniqid():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def enum(**enums):
    return type('Enum', (), enums)

LinkRel = enum(SETUP=u'setup', MANAGE = u'manage', SUPPORT = u'support', DELETION_POLICY = u'deletion-policy')
ExtensionType = enum(LINK=u'link', OPENID=u'openIdRealm', CONTEXT_EXTRACTOR=u'contextExtractor', GADGET=u'gadget')

class MixedClassMeta(type):
    '''
    Borrowed from http://stackoverflow.com/questions/6098970/are-mixin-class-init-functions-not-automatically-called-in-python
    '''
    
    def __new__(cls, name, bases, classdict):
        classinit = classdict.get('__init__')  # could be None
        # define an __init__ function for the new class
        def __init__(self, *args, **kwargs):
            # call the __init__ functions of all the bases
            for base in type(self).__bases__:
                base.__init__(self, *args, **kwargs)
            # also call any __init__ function that was in the new class
            if classinit:  classinit(self, *args, **kwargs)
        # add the local function to the new class
        classdict['__init__'] = __init__
        return type.__new__(cls, name, bases, classdict)

class IdMixin(object):
    
    def __init__(self, *args, **kwargs):
        self._id = _uniqid()
    
    @property
    def identity(self):
        return self._id
    
class URLMixin(object):
    
    def __init__(self, url, *args, **kwargs):
        self._url = url
        
    @property
    def url(self):
        return self._url
    
class UniqueURLMixin(URLMixin):
    
    def __init__(self, url, *args, **kwargs):
        super(UniqueURLMixin, self).__init__(url, *args, **kwargs)
        
    @property
    def url(self):
        return self._url
    
    def __eq__(self, other):
        return self.url == other.url
    
    def __ne__(self, other):
        return self.url != other.url
    
    def __hash__(self):
        return hash(self.url)
    
class HasScopesMixin(object):
    
    def __init__(self, *args, **kwargs):
        self._scopes = set()
    
    def add_scope(self, scope):
        self._scopes.add(scope)
        
    @property
    def scopes(self):
        return self._scopes
    
class Support(object):
    
    def __init__(self, rel, href):
        self.rel = rel
        self.href = href
        
    def __eq__(self, other):
        return self.rel == other.rel
    
    def __ne__(self, other):
        return self.rel != other.rel
    
    def __hash__(self):
        return hash(self.rel)
        
class Scope(UniqueURLMixin, IdMixin):
    __metaclass__ = MixedClassMeta
    
    def __init__(self, url, reason, *args, **kwargs):
        self.reason = reason
        
class Extension(IdMixin):
    
    def __init__(self, extension_type, *args, **kwargs):
        super(Extension, self).__init__(extension_type, *args, **kwargs)
        self.type = extension_type
        self.container_name = None
        
class OpenIdRealm(Extension, URLMixin):
    
    def __init__(self, url, *args, **kwargs):
        super(OpenIdRealm, self).__init__(ExtensionType.OPENID, url, *args, **kwargs)
        URLMixin.__init__(self, url, *args, **kwargs)
        
class Link(Extension, URLMixin, HasScopesMixin):
    
    def __init__(self, url, *args, **kwargs):
        super(Link, self).__init__(ExtensionType.LINK, url, *args, **kwargs)
        URLMixin.__init__(self, url, *args, **kwargs)
        HasScopesMixin.__init__(self, *args, **kwargs)
    
class ContextualGadget(Extension, HasScopesMixin, UniqueURLMixin):
    
    def __init__(self, url, name, *args, **kwargs):
        super(ContextualGadget, self).__init__(ExtensionType.GADGET, url, name, *args, **kwargs)
        HasScopesMixin.__init__(self, *args, **kwargs)
        UniqueURLMixin.__init__(self, url, *args, **kwargs)
        self.container_name = "mail"
        self.name = name
        
class ContextExtractor(Extension, HasScopesMixin, URLMixin):
    
    class Param(object):
        
        def __init__(self, name, value):
            self.name = name
            self.value = value
    
    def __init__(self, url, name, *args, **kwargs):
        super(ContextExtractor, self).__init__(ExtensionType.CONTEXT_EXTRACTOR, url, name, *args, **kwargs)
        HasScopesMixin.__init__(self, *args, **kwargs)
        URLMixin.__init__(self, url, *args, **kwargs)
        self.name = name
        self.container_name = "mail"
        self._triggers = set()
        self._params = []
        
    def add_trigger(self, extension):
        self._triggers.add(extension)
        
    def add_param(self, name, value):
        self._params.append(ContextExtractor.Param(name, value))
        
    @property
    def triggers(self):
        return self._triggers
    
    @property
    def params(self):
        return self._params

class Manifest(HasScopesMixin):
    __metaclass__ = MixedClassMeta
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.extensions = set()
        self.supports = set()
        
    @property
    def scopes(self):
        cu_scopes = super(Manifest, self).scopes
        for x in self.extensions:
            if hasattr(x, "scopes"):
                cu_scopes.update(x.scopes)
        return cu_scopes
        
    def add_extension(self, gadget):
        self.extensions.add(gadget)
        
    def add_support(self, support):
        self.supports.add(support)

