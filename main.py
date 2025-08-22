import falcon
from falcon import Request, Response
from falcon.asgi import App
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Date, Time, func
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import Environment, FileSystemLoader
import datetime
from datetime import timedelta
import uuid
from functools import wraps
import os

# Jinja2 setup
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(template_dir))

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine("sqlite:///keystone.db")
Session = scoped_session(sessionmaker(bind=engine))

# Middleware
class SimpleLoggerMiddleware:
    async def process_request(self, req: Request, resp: Response):
        print(f"[{req.method}] {req.path} - {req.remote_addr}")

    async def process_response(self, req: Request, resp: Response, resource, req_succeeded):
        print(f"Response status: {resp.status}")

class CORSMiddleware:
    async def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        resp.set_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')

# Falcon app
app = App(middleware=[SimpleLoggerMiddleware(), CORSMiddleware()])

# Models (unchanged)
class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    login = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Page(Base):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class ContentBlock(Base):
    __tablename__ = 'content_blocks'
    id = Column(Integer, primary_key=True)
    page_slug = Column(String, ForeignKey('pages.slug', ondelete='CASCADE'), nullable=False)
    identifier = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Servant(Base):
    __tablename__ = 'servants'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(String(50), nullable=True, unique=True)
    role = Column(Text, nullable=True)
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Parishioner(Base):
    __tablename__ = 'parishioners'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(String(50), nullable=True, unique=True)
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    identifier = Column(String(255), nullable=False, unique=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    location = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    servant_id = Column(Integer, ForeignKey('servants.id', ondelete='CASCADE'), nullable=False)
    parishioner_id = Column(Integer, ForeignKey('parishioners.id', ondelete='CASCADE'), nullable=False)

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)
    location = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    servant_id = Column(Integer, ForeignKey('servants.id', ondelete='CASCADE'), nullable=False)
    parishioner_id = Column(Integer, ForeignKey('parishioners.id', ondelete='CASCADE'), nullable=False)

class New(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    identifier = Column(String(255), nullable=False, unique=True)
    title = Column(String(320), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(320), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class SessionToken(Base):
    __tablename__ = 'session_tokens'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admins.id'))
    token = Column(String, unique=True)
    created_at = Column(DateTime)
    last_active = Column(DateTime)
    admin = relationship("Admin")

class Need(Base):
    __tablename__ = 'needs'
    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False)
    title = Column(String(400), nullable=False)
    content = Column(Text, nullable=False)
    email = Column(String(60), nullable=False)
    phone = Column(String(15), nullable=True)
    name = Column(String(120), nullable=False)
    surname = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

# Authentication decorator using cookies
def login_required(func):
    @wraps(func)
    async def wrapper(self, req, resp, *args, **kwargs):
        token = req.get_cookie('auth_token')
        if not token:
            template = env.get_template('error.html')
            resp.status = falcon.HTTP_401
            resp.content_type = 'text/html'
            resp.text = template.render(error='Please login to access this page')
            return

        session = Session()
        try:
            session_token = session.query(SessionToken).filter_by(token=token).first()
            if not session_token:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_403
                resp.content_type = 'text/html'
                resp.text = template.render(error='Invalid or expired token')
                return

            if session_token.last_active and (datetime.datetime.utcnow() - session_token.last_active) > datetime.timedelta(minutes=60):
                session.delete(session_token)
                session.commit()
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_403
                resp.content_type = 'text/html'
                resp.text = template.render(error='Session expired')
                return

            session_token.last_active = datetime.datetime.utcnow()
            session.commit()
            req.context.user = session_token.admin
            return await func(self, req, resp, *args, **kwargs)
        finally:
            session.close()

    return wrapper

# Resources

class HomeResource:
    async def on_get(self, req: Request, resp: Response):
        template = env.get_template('home.html')
        resp.content_type = 'text/html'
        resp.text = template.render(message="Welcome to the Parish Management System!")

class LoginResource:
    async def on_get(self, req, resp):
        template = env.get_template('login.html')
        resp.content_type = 'text/html'
        resp.text = template.render()

    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media
            login = data.get('login')
            password = data.get('password')

            if not login or not password:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='Login and password are required')
                return

            admin = session.query(Admin).filter_by(login=login).first()
            if not admin or not admin.check_password(password):
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_401
                resp.content_type = 'text/html'
                resp.text = template.render(error='Invalid login or password')
                return

            token = str(uuid.uuid4())
            new_token = SessionToken(
                admin_id=admin.id,
                token=token,
                created_at=datetime.datetime.utcnow(),
                last_active=datetime.datetime.utcnow()
            )
            session.add(new_token)
            session.commit()

            resp.set_cookie('auth_token', token, max_age=3600, path='/')
            template = env.get_template('home.html')
            resp.content_type = 'text/html'
            resp.text = template.render(message=f"Welcome, {admin.login}!")

        except Exception as e:
            import traceback
            resp.status = falcon.HTTP_500
            resp.content_type = 'text/plain'
            resp.text = traceback.format_exc()
        finally:
            session.close()

class LogoutResource:
    async def on_post(self, req, resp):
        token = req.get_cookie('auth_token')
        if not token:
            template = env.get_template('login.html')
            resp.content_type = 'text/html'
            resp.text = template.render(message='You are not logged in')
            return

        session = Session()
        try:
            session_token = session.query(SessionToken).filter_by(token=token).first()
            if session_token:
                session.delete(session_token)
                session.commit()
            resp.unset_cookie('auth_token')
            template = env.get_template('login.html')
            resp.content_type = 'text/html'
            resp.text = template.render(message='Logged out successfully')
        finally:
            session.close()

class AdminResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            admins = session.query(Admin).all()
            template = env.get_template('admins_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(admins=admins)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            login = data.get("login")
            password = data.get("password")
            if not login or not password:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='Login and password are required')
                return
            admin = Admin(login=login)
            admin.set_password(password)
            session.add(admin)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/admins'
        finally:
            session.close()

class AdminDetailResource:
    @login_required
    async def on_get(self, req, resp, admin_id):
        session = Session()
        try:
            admin = session.query(Admin).get(admin_id)
            if not admin:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Admin not found')
                return
            template = env.get_template('admin_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(admin=admin)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, admin_id):
        session = Session()
        try:
            data = await req.media()
            admin = session.query(Admin).get(admin_id)
            if not admin:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Admin not found')
                return
            admin.login = data.get("login", admin.login)
            password = data.get("password")
            if password:
                admin.set_password(password)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/admins/{admin_id}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, admin_id):
        session = Session()
        try:
            admin = session.query(Admin).get(admin_id)
            if not admin:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Admin not found')
                return
            session.delete(admin)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/admins'
        finally:
            session.close()

class PageResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            pages = session.query(Page).all()
            template = env.get_template('pages_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(pages=pages)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            title = data.get("title")
            slug = data.get("slug")
            if not title or not slug:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='Title and slug are required')
                return
            page = Page(title=title, slug=slug)
            session.add(page)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/pages'
        finally:
            session.close()

class PageDetailResource:
    @login_required
    async def on_get(self, req, resp, slug):
        session = Session()
        try:
            page = session.query(Page).filter_by(slug=slug).first()
            if not page:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Page not found')
                return
            template = env.get_template('page_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(page=page)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, slug):
        session = Session()
        try:
            data = await req.media()
            page = session.query(Page).filter_by(slug=slug).first()
            if not page:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Page not found')
                return
            page.title = data.get("title", page.title)
            page.slug = data.get("slug", page.slug)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/pages/{page.slug}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, slug):
        session = Session()
        try:
            page = session.query(Page).filter_by(slug=slug).first()
            if not page:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Page not found')
                return
            session.delete(page)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/pages'
        finally:
            session.close()

class ContentBlockResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            content_blocks = session.query(ContentBlock).all()
            template = env.get_template('content_blocks_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(content_blocks=content_blocks)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            page_slug = data.get('page_slug')
            identifier = data.get('identifier')
            content = data.get('content')
            if not page_slug or not identifier or not content:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='All fields are required')
                return
            content_block = ContentBlock(page_slug=page_slug, identifier=identifier, content=content)
            session.add(content_block)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/content_blocks'
        finally:
            session.close()

class ContentBlockDetailResource:
    @login_required
    async def on_get(self, req, resp, identifier):
        session = Session()
        try:
            content_block = session.query(ContentBlock).filter_by(identifier=identifier).first()
            if not content_block:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Content Block not found')
                return
            template = env.get_template('content_block_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(content_block=content_block)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, identifier):
        session = Session()
        try:
            data = await req.media()
            content_block = session.query(ContentBlock).filter_by(identifier=identifier).first()
            if not content_block:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Content Block not found')
                return
            content_block.page_slug = data.get('page_slug', content_block.page_slug)
            content_block.identifier = data.get('identifier', content_block.identifier)
            content_block.content = data.get('content', content_block.content)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/content_blocks/{content_block.identifier}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, identifier):
        session = Session()
        try:
            content_block = session.query(ContentBlock).filter_by(identifier=identifier).first()
            if not content_block:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Content Block not found')
                return
            session.delete(content_block)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/content_blocks'
        finally:
            session.close()

class ServantResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            servants = session.query(Servant).all()
            template = env.get_template('servants_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(servants=servants)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            name = data.get('name')
            surname = data.get('surname')
            email = data.get('email')
            phone = data.get('phone')
            role = data.get('role')
            birth_date = data.get('birth_date')
            if not name or not surname:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='Name and surname are required')
                return
            servant = Servant(name=name, surname=surname, email=email, phone=phone, role=role, birth_date=birth_date)
            session.add(servant)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/servants'
        finally:
            session.close()

class ServantDetailResource:
    @login_required
    async def on_get(self, req, resp, servant_id):
        session = Session()
        try:
            servant = session.query(Servant).get(servant_id)
            if not servant:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Servant not found')
                return
            template = env.get_template('servant_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(servant=servant)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, servant_id):
        session = Session()
        try:
            data = await req.media()
            servant = session.query(Servant).get(servant_id)
            if not servant:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Servant not found')
                return
            servant.name = data.get('name', servant.name)
            servant.surname = data.get('surname', servant.surname)
            servant.email = data.get('email', servant.email)
            servant.phone = data.get('phone', servant.phone)
            servant.role = data.get('role', servant.role)
            servant.birth_date = data.get('birth_date', servant.birth_date)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/servants/{servant_id}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, servant_id):
        session = Session()
        try:
            servant = session.query(Servant).get(servant_id)
            if not servant:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Servant not found')
                return
            session.delete(servant)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/servants'
        finally:
            session.close()

class ParishionerResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            parishioners = session.query(Parishioner).all()
            template = env.get_template('parishioners_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(parishioners=parishioners)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            name = data.get('name')
            surname = data.get('surname')
            email = data.get('email')
            phone = data.get('phone')
            birth_date = data.get('birth_date')
            if not name or not surname:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='Name and surname are required')
                return
            parishioner = Parishioner(name=name, surname=surname, email=email, phone=phone, birth_date=birth_date)
            session.add(parishioner)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/parishioners'
        finally:
            session.close()

class ParishionerDetailResource:
    @login_required
    async def on_get(self, req, resp, parishioner_id):
        session = Session()
        try:
            parishioner = session.query(Parishioner).get(parishioner_id)
            if not parishioner:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Parishioner not found')
                return
            template = env.get_template('parishioner_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(parishioner=parishioner)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, parishioner_id):
        session = Session()
        try:
            data = await req.media()
            parishioner = session.query(Parishioner).get(parishioner_id)
            if not parishioner:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Parishioner not found')
                return
            parishioner.name = data.get('name', parishioner.name)
            parishioner.surname = data.get('surname', parishioner.surname)
            parishioner.email = data.get('email', parishioner.email)
            parishioner.phone = data.get('phone', parishioner.phone)
            parishioner.birth_date = data.get('birth_date', parishioner.birth_date)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/parishioners/{parishioner_id}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, parishioner_id):
        session = Session()
        try:
            parishioner = session.query(Parishioner).get(parishioner_id)
            if not parishioner:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Parishioner not found')
                return
            session.delete(parishioner)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/parishioners'
        finally:
            session.close()

class ServiceResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            services = session.query(Service).all()
            template = env.get_template('services_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(services=services)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            title = data.get('title')
            description = data.get('description')
            identifier = data.get('identifier')
            date = data.get('date')
            time = data.get('time')
            location = data.get('location')
            servant_id = data.get('servant_id')
            parishioner_id = data.get('parishioner_id')
            if not title or not description or not identifier or not date or not time or not location or not servant_id or not parishioner_id:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='All fields are required')
                return
            service = Service(title=title, description=description, identifier=identifier, date=date, time=time, location=location, servant_id=servant_id, parishioner_id=parishioner_id)
            session.add(service)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/services'
        finally:
            session.close()

class ServiceDetailResource:
    @login_required
    async def on_get(self, req, resp, identifier):
        session = Session()
        try:
            service = session.query(Service).filter_by(identifier=identifier).first()
            if not service:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Service not found')
                return
            template = env.get_template('service_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(service=service)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, identifier):
        session = Session()
        try:
            data = await req.media()
            service = session.query(Service).filter_by(identifier=identifier).first()
            if not service:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Service not found')
                return
            service.title = data.get('title', service.title)
            service.description = data.get('description', service.description)
            service.identifier = data.get('identifier', service.identifier)
            service.date = data.get('date', service.date)
            service.time = data.get('time', service.time)
            service.location = data.get('location', service.location)
            service.servant_id = data.get('servant_id', service.servant_id)
            service.parishioner_id = data.get('parishioner_id', service.parishioner_id)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/services/{service.identifier}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, identifier):
        session = Session()
        try:
            service = session.query(Service).filter_by(identifier=identifier).first()
            if not service:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Service not found')
                return
            session.delete(service)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/services'
        finally:
            session.close()

class EventResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            events = session.query(Event).all()
            template = env.get_template('events_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(events=events)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            identifier = data.get('identifier')
            title = data.get('title')
            description = data.get('description')
            date = data.get('date')
            time = data.get('time')
            location = data.get('location')
            servant_id = data.get('servant_id')
            parishioner_id = data.get('parishioner_id')
            if not identifier or not title or not description or not date or not location or not servant_id or not parishioner_id:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='All required fields must be filled')
                return
            event = Event(identifier=identifier, title=title, description=description, date=date, time=time, location=location, servant_id=servant_id, parishioner_id=parishioner_id)
            session.add(event)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/events'
        finally:
            session.close()

class EventDetailResource:
    @login_required
    async def on_get(self, req, resp, identifier):
        session = Session()
        try:
            event = session.query(Event).filter_by(identifier=identifier).first()
            if not event:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Event not found')
                return
            template = env.get_template('event_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(event=event)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, identifier):
        session = Session()
        try:
            data = await req.media()
            event = session.query(Event).filter_by(identifier=identifier).first()
            if not event:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Event not found')
                return
            event.identifier = data.get('identifier', event.identifier)
            event.title = data.get('title', event.title)
            event.description = data.get('description', event.description)
            event.date = data.get('date', event.date)
            event.time = data.get('time', event.time)
            event.location = data.get('location', event.location)
            event.servant_id = data.get('servant_id', event.servant_id)
            event.parishioner_id = data.get('parishioner_id', event.parishioner_id)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/events/{event.identifier}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, identifier):
        session = Session()
        try:
            event = session.query(Event).filter_by(identifier=identifier).first()
            if not event:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Event not found')
                return
            session.delete(event)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/events'
        finally:
            session.close()

class NewResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            news = session.query(New).all()
            template = env.get_template('news_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(news=news)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            identifier = data.get('identifier')
            title = data.get('title')
            content = data.get('content')
            if not identifier or not title or not content:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='All fields are required')
                return
            new = New(identifier=identifier, title=title, content=content)
            session.add(new)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/news'
        finally:
            session.close()

class NewDetailResource:
    @login_required
    async def on_get(self, req, resp, identifier):
        session = Session()
        try:
            new = session.query(New).filter_by(identifier=identifier).first()
            if not new:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='New not found')
                return
            template = env.get_template('new_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(new=new)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, identifier):
        session = Session()
        try:
            data = await req.media()
            new = session.query(New).filter_by(identifier=identifier).first()
            if not new:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='New not found')
                return
            new.identifier = data.get('identifier', new.identifier)
            new.title = data.get('title', new.title)
            new.content = data.get('content', new.content)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/news/{new.identifier}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, identifier):
        session = Session()
        try:
            new = session.query(New).filter_by(identifier=identifier).first()
            if not new:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='New not found')
                return
            session.delete(new)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/news'
        finally:
            session.close()

class PostResource:
    @login_required
    async def on_get(self, req, resp):
        session = Session()
        try:
            posts = session.query(Post).all()
            template = env.get_template('posts_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(posts=posts)
        finally:
            session.close()

    @login_required
    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            title = data.get('title')
            content = data.get('content')
            if not title or not content:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='Title and content are required')
                return
            post = Post(title=title, content=content)
            session.add(post)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/posts'
        finally:
            session.close()

class PostDetailResource:
    @login_required
    async def on_get(self, req, resp, post_id):
        session = Session()
        try:
            post = session.query(Post).get(post_id)
            if not post:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Post not found')
                return
            template = env.get_template('post_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(post=post)
        finally:
            session.close()

    @login_required
    async def on_put(self, req, resp, post_id):
        session = Session()
        try:
            data = await req.media()
            post = session.query(Post).get(post_id)
            if not post:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Post not found')
                return
            post.title = data.get('title', post.title)
            post.content = data.get('content', post.content)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/posts/{post_id}'
        finally:
            session.close()

    @login_required
    async def on_delete(self, req, resp, post_id):
        session = Session()
        try:
            post = session.query(Post).get(post_id)
            if not post:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Post not found')
                return
            session.delete(post)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/posts'
        finally:
            session.close()

class NeedResource:
    async def on_get(self, req, resp):
        session = Session()
        try:
            needs = session.query(Need).all()
            template = env.get_template('needs_list.html')
            resp.content_type = 'text/html'
            resp.text = template.render(needs=needs)
        finally:
            session.close()

    async def on_post(self, req, resp):
        session = Session()
        try:
            data = await req.media()
            title = data.get('title')
            content = data.get('content')
            email = data.get('email')
            phone = data.get('phone')
            name = data.get('name')
            surname = data.get('surname')
            if not title or not content or not email or not name or not surname:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_400
                resp.content_type = 'text/html'
                resp.text = template.render(error='All required fields must be filled')
                return
            token = str(uuid.uuid4())
            need = Need(token=token, title=title, content=content, email=email, phone=phone, name=name, surname=surname)
            session.add(need)
            session.commit()
            template = env.get_template('need_created.html')
            resp.content_type = 'text/html'
            resp.text = template.render(token=token)
        finally:
            session.close()

class NeedDetailResource:
    async def on_get(self, req, resp, token):
        session = Session()
        try:
            need = session.query(Need).filter_by(token=token).first()
            if not need:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Need not found')
                return
            template = env.get_template('need_detail.html')
            resp.content_type = 'text/html'
            resp.text = template.render(need=need)
        finally:
            session.close()

    async def on_put(self, req, resp, token):
        session = Session()
        try:
            data = await req.media()
            need = session.query(Need).filter_by(token=token).first()
            if not need:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Need not found')
                return
            need.title = data.get('title', need.title)
            need.content = data.get('content', need.content)
            need.email = data.get('email', need.email)
            need.phone = data.get('phone', need.phone)
            need.name = data.get('name', need.name)
            need.surname = data.get('surname', need.surname)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = f'/needs/{token}'
        finally:
            session.close()

    async def on_delete(self, req, resp, token):
        session = Session()
        try:
            need = session.query(Need).filter_by(token=token).first()
            if not need:
                template = env.get_template('error.html')
                resp.status = falcon.HTTP_404
                resp.content_type = 'text/html'
                resp.text = template.render(error='Need not found')
                return
            session.delete(need)
            session.commit()
            resp.status = falcon.HTTP_303
            resp.location = '/needs'
        finally:
            session.close()

# Routes
app.add_route("/home", HomeResource())
app.add_route("/admins", AdminResource())
app.add_route("/admins/{admin_id:int}", AdminDetailResource())
app.add_route("/pages", PageResource())
app.add_route("/pages/{slug}", PageDetailResource())
app.add_route("/content_blocks", ContentBlockResource())
app.add_route("/content_blocks/{identifier}", ContentBlockDetailResource())
app.add_route("/servants", ServantResource())
app.add_route("/servants/{servant_id:int}", ServantDetailResource())
app.add_route("/parishioners", ParishionerResource())
app.add_route("/parishioners/{parishioner_id:int}", ParishionerDetailResource())
app.add_route("/services", ServiceResource())
app.add_route("/services/{identifier}", ServiceDetailResource())
app.add_route("/events", EventResource())
app.add_route("/events/{identifier}", EventDetailResource())
app.add_route("/news", NewResource())
app.add_route("/news/{identifier}", NewDetailResource())
app.add_route("/posts", PostResource())
app.add_route("/posts/{post_id:int}", PostDetailResource())
app.add_route('/login', LoginResource())
app.add_route('/logout', LogoutResource())
app.add_route('/needs', NeedResource())
app.add_route('/needs/{token}', NeedDetailResource())

# DB init
Base.metadata.create_all(engine)