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
        self.engine.index_document(title="private A", text="private employment record alpha", collection_id="shared", source_id="source-a", is_private=True)
        self.engine.index_document(title="private B", text="private employment record beta", collection_id="shared", source_id="source-b", is_private=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_private_documents_are_hidden_by_default(self):
        self.assertEqual(self.engine.search(query="employment"), [])

    def test_grant_is_scoped_to_collection_purpose_and_source(self):
        grant = self.consent.grant_local_access(source_id="source-a", collection_id="shared",
                                                purpose="my own records", granted_by="local-owner", expires_in_hours=2)
        self.assertIsNone(self.consent.authorize(grant_id=grant["grant_id"], purpose="other purpose"))
        authorized = self.consent.authorize(grant_id=grant["grant_id"], purpose="my own records")
        results = self.engine.search(query="employment", authorized_collection=authorized["collection_id"],
                                     authorized_source=authorized["source_id"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_id"], "source-a")

    def test_grant_cannot_expose_another_source_in_same_collection(self):
        grant = self.consent.grant_local_access(source_id="source-a", collection_id="shared",
                                                purpose="review own files", granted_by="local-owner")
        results = self.engine.search(query="employment", authorized_collection=grant["collection_id"],
                                     authorized_source=grant["source_id"])
        self.assertEqual({row["source_id"] for row in results}, {"source-a"})

    def test_revoke_removes_access(self):
        grant = self.consent.grant_local_access(source_id="source-a", collection_id="shared",
                                                purpose="review own files", granted_by="local-owner")
        self.assertTrue(self.consent.revoke(grant["grant_id"], "local-owner"))
        self.assertIsNone(self.consent.authorize(grant_id=grant["grant_id"], purpose="review own files"))

    def test_profile_settings_persist(self):
        saved = self.store.save_profile(profile_id="default", display_name="Local", locale="fr",
                                        languages=["fr", "en"], default_collections=["pub"], result_format="json")
        loaded = self.store.get_profile("default")
        self.assertEqual(saved["locale"], loaded["locale"])
        self.assertEqual(loaded["languages"], ["fr", "en"])


if __name__ == "__main__":
    unittest.main()
