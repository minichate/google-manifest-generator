import unittest
import __init__ as m

class ManifestTest(unittest.TestCase):
    
    def setUp(self):
        self.manifest = m.Manifest("Test", "Description")
    
    def tearDown(self):
        self.manifest = None
    
    def test_duplicate_scopes(self):
        gadget = m.ContextualGadget("Test", "http://test/gadget.xml")
        s1 = m.Scope("http://test", "Test")
        s2 = m.Scope("http://test", "Test")
        gadget.add_scope(s1)
        gadget.add_scope(s2)
        
        self.manifest.add_extension(gadget)
        
        scopes = self.manifest.scopes
        self.assertEqual(1, len(scopes))
        self.assertSetEqual(set([s1]), scopes)
        
    def test_cached_scope_id(self):
        s1 = m.Scope("http://test", "Test")
        id1 = s1.identity
        id2 = s1.identity
        self.assertEquals(id1, id2)
        
    def test_scope_equality_same(self):
        s1 = m.Scope("http://test", "Test")
        s2 = m.Scope("http://test", "Test")
        
        self.assertEqual(s1, s2)
        
    def test_scope_equality_diff_url(self):
        s1 = m.Scope("http://test", "Test")
        s2 = m.Scope("http://other/", "Test")
        
        self.assertNotEqual(s1, s2)
        
    def test_scope_equality_diff_desc(self):
        s1 = m.Scope("http://test", "Test")
        s2 = m.Scope("http://test", "Other Test")
        
        self.assertEqual(s1, s2)
        
    def test_duplicate_gadgets(self):
        g1 = m.ContextualGadget("Test", "http://test/gadget.xml")
        g2 = m.ContextualGadget("Test", "http://test/gadget.xml")
        
        self.manifest.add_extension(g1)
        self.manifest.add_extension(g2)
        
        self.assertSetEqual(set([g1]), self.manifest.extensions)
        
    def test_manifest_scopes(self):
        s1 = m.Scope("http://test", "Test")
        self.manifest.add_scope(s1)
        self.assertSetEqual(set([s1]), self.manifest.scopes)
        
    def test_manifest_gadget_scopes_mix(self):
        s1 = m.Scope("http://google.com", "For fun")
        s2 = m.Scope("http://sheepdog", "For fun")
        
        gadget = m.ContextualGadget("Test", "http://test/gadget.xml")
        gadget.add_scope(s1)
        self.manifest.add_extension(gadget)
        
        self.manifest.add_scope(s2)
        
        expected = set([s1, s2])
        actual = self.manifest.scopes
        
        self.assertSetEqual(expected, actual)
        
if __name__ == '__main__':
    unittest.main()