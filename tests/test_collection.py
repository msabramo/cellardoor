import unittest
import mongoengine as me
from bson.objectid import ObjectId
from hammock import Collection

class TestDoc(me.Document):
	name = me.StringField()
	another_field = me.IntField()


me.connect('hammock_test')


class TestCollection(unittest.TestCase):

	def setUp(self):
		TestDoc.objects().delete()


	def generate_collection(self, n=20):
		class TestDocs(Collection):
			document = TestDoc

		docs = []
		for i in range(0, n):
			doc = TestDoc(name='doc#%02d' % i, another_field=n-i)
			doc.save()
			docs.append(doc)

		return TestDocs, docs


	def test_identity(self):
		class TestDocs(Collection):
			document = TestDoc

		identity = {'foo':'bar'}
		testdocs = TestDocs(identity)
		self.assertEquals(testdocs.identity, identity)


	def test_list_limits_and_skip(self):
		TestDocs, docs = self.generate_collection(n=20)

		self.assertEquals(TestDoc.objects().count(), 20)
		
		TestDocs.default_limit = 10
		TestDocs.max_limit = 15
		testdocs = TestDocs()

		# No limit argument fetches the default limit
		results = list(testdocs.list())
		self.assertEquals(len(results), testdocs.default_limit)

		# The limit argument works
		results = list(testdocs.list(limit=5))
		self.assertEquals(len(results), 5)

		results = list(testdocs.list(limit=15))
		self.assertEquals(len(results), 15)

		# max_limit is the ceiling regardless of the limits arg
		results = list(testdocs.list(limit=100))
		self.assertEquals(len(results), 15)

		# skip works
		results = list(testdocs.list(skip=3, limit=1))
		self.assertEquals(results[0].name, 'doc#03')


	def test_list_fields(self):
		TestDoc(name='foo', another_field=23).save()
		
		class TestDocs(Collection):
			document = TestDoc

		testdocs = TestDocs()

		# include_fields exclusively includes the listed fields
		doc = testdocs.list(include_fields=('name',)).first().to_mongo()
		self.assertEquals(doc.get('name'), 'foo')
		self.assertEquals(doc.get('another_field'), None)

		# exclude fields excludes only the listed fields
		doc = testdocs.list(exclude_fields=('name',)).first().to_mongo()
		self.assertEquals(doc.get('name'), None)
		self.assertEquals(doc.get('another_field'), 23)

		# exclude overrides include
		doc = testdocs.list(include_fields=('name',), exclude_fields=('name',)).first().to_mongo()
		self.assertEquals(doc.get('name'), None)
		self.assertEquals(doc.get('another_field'), 23)		


	def test_list_sort(self):
		TestDocs, docs = self.generate_collection(n=20)
		testdocs = TestDocs()

		# ascending by name
		doc = testdocs.list(sort=('+name',)).first()
		self.assertEquals(doc.id, docs[0].id)

		# descending by name
		doc = testdocs.list(sort=('-name',)).first()
		self.assertEquals(doc.id, docs[19].id)

		# ascending by another_field
		doc = testdocs.list(sort=('+another_field',)).first()
		self.assertEquals(doc.id, docs[19].id)

		# descending by another_field
		doc = testdocs.list(sort=('-another_field',)).first()
		self.assertEquals(doc.id, docs[0].id)


	def test_list_filter(self):
		TestDocs, docs = self.generate_collection(n=20)
		testdocs = TestDocs()

		# simple equality filter
		results = list(testdocs.list(filter={'name': 'doc#04'}))
		self.assertEquals(len(results), 1)
		self.assertEquals(results[0].id, docs[4].id)

		# complex command
		results = list(testdocs.list(filter={'another_field': {'$lt':5}}))
		self.assertEquals(len(results), 4)


	def test_list_complex(self):
		TestDocs, docs = self.generate_collection(n=20)
		testdocs = TestDocs()

		results = list(testdocs.list(
			filter={'another_field': {'$lt':5}},
			sort=('-another_field',),
			include_fields=('name',),
			skip=2,
			limit=2
		))

		self.assertEquals(len(results), 2)
		self.assertEquals(results[0].id, docs[18].id)


	def test_get(self):
		TestDocs, docs = self.generate_collection(n=20)
		testdocs = TestDocs()

		doc = testdocs.get(docs[5].id)
		self.assertEquals(doc.id, docs[5].id)


	def test_get_fields(self):
		TestDocs, docs = self.generate_collection(n=20)
		testdocs = TestDocs()

		doc = testdocs.get(docs[5].id, include_fields=('name',)).to_mongo()
		self.assertEquals(doc.get('name'), docs[5].name)
		self.assertEquals(doc.get('another_field'), None)

		doc = testdocs.get(docs[5].id, exclude_fields=('name',)).to_mongo()
		self.assertEquals(doc.get('name'), None)
		self.assertEquals(doc.get('another_field'), docs[5].another_field)


	def test_create(self):
		class TestDocs(Collection):
			document = TestDoc

		testdocs = TestDocs()
		
		# should fail if a field doesn't validate
		with self.assertRaises(me.ValidationError):
			doc = testdocs.create({'name':'foo', 'another_field': 'not an int'})

		doc = testdocs.create({'name':'foo', 'another_field': 123})

		# we create one and only one doc per create() and save it to the database
		num_docs = testdocs.list().count()
		self.assertEquals(num_docs, 1)
		
		self.assertIsInstance(doc.id, ObjectId)
		self.assertEquals(doc.name, 'foo')
		self.assertEquals(doc.another_field, 123)

