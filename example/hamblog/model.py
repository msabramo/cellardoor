import re
from datetime import datetime
from hammock.model import *


class Slug(Text):
	
	def __init__(self, *args, **kwargs):
		super(Slug, self).__init__(maxlength=50, regex=re.compile('^[\w\-]+$', re.UNICODE))


class BaseModel(Model):
	created = DateTime(required=True)
	modified = DateTime(required=True)
	
	def before_create(self):
		self.modified = self.created = datetime.utcnow()
		super(BaseModel, self).before_create()
		
		
	def before_update(self):
		self.modified = datetime.utcnow()
		super(BaseModel, self).before_update()


class Person(BaseModel):
	first_name = Text(maxlength=50, required=True)
	last_name = Text(maxlength=50, required=True)
	email = Email(required=True, hidden=True)
	password = Text(maxlength=50, hidden=True)
	role = Enum('anonymous', 'normal', 'admin', default='anonymous')
	posts = Many('Post', inverse='author')
	token = Group(
		value=Text(maxlength=150, required=True),
		expires=DateTime(required=True)
	)
	
	
class Post(BaseModel):
	status = Enum('draft', 'published', default='draft')
	publish_date = DateTime()
	slug = Slug(required=True),
	author = One(Person, inverse='posts', embedded=True, required=True)
	title = Text(maxlength=200, required=True)
	content = Text(maxlength=10000)
	tags = Many('Tag', inverse='posts', embedded=True)
	
	
class Tag(Model):
	name = Text(maxlength=50, required=True)
	slug = Slug(required=True)
	posts = Many(Post, inverse='tags')
	