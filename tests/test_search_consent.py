import tempfile
import unittest
from pathlib import Path

from app.consent import ConsentManager
from app.search_engine import LocalSearchEngine
from app.storage import SQLiteStore


class SearchAndConsentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / "test.sqlite3")
        self.engine = LocalSearchEngine(self.store)
        self.consent = ConsentManager(self.store)
        self.engine.index_document(title="public", text="weather outlook", collection_id="pub", source_id="web", is_private=False)
        self.engine.index_document(title="private", text="private employment record", collection_id="private", source_id="owned", is_private=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_private_documents_are_hidden_by_default(self):
        self.assertEqual(self.engine.search(query="employment"), [])

    def test_grant_is_scoped_to_collection_and_purpose(self):
        grant = self.consent.grant_local_access(source_id="owned", collection_id="private",
                                                purpose="my own records", granted_by="local-owner", expires_in_hours=2)
        self.assertIsNone(self.consent.authorize(grant_id=grant["grant_id"], purpose="other purpose"))
        authorized = self.consent.authorize(grant_id=grant["grant_id"], purpose="my own records")
        self.assertIsNotNone(authorized)
        results = self.engine.search(query="employment", authorized_collection=authorized["collection_id"])
        self.assertEqual(len(results), 1)

    def test_revoke_removes_access(self):
        grant = self.consent.grant_local_access(source_id="owned", collection_id="private",
                                                purpose="review own files", granted_by="local-owner")
        self.assertTrue(self.consent.revoke(grant["grant_id"], "local-owner"))
        self.assertIsNone(self.consent.authorize(grant_id=grant["grant_id"], purpose="review own files"))


if __name__ == "__main__":
    unittest.main()
