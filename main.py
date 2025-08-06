import falcon
from falcon import Request, Response
from falcon.asgi import App
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Date, Time, func
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship
from werkzeug.security import generate_password_hash, check_password_hash
import json
import datetime

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


# Falcon app
app = App(middleware=[SimpleLoggerMiddleware()])

# Models
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


# Resource handlers
class HomeResource:
    async def on_get(self, req: Request, resp: Response):
        resp.media = {"message": "Простой CRUD на Falcon и SQLAlchemy!"}


class AdminResource:
    async def on_get(self, req, resp):
        session = Session()
        admins = session.query(Admin).all()
        data = [{"id": a.id, "login": a.login} for a in admins]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        session = Session()
        data = await req.media
        login = data.get("login")
        password = data.get("password")
        admin = Admin(login=login)
        admin.set_password(password)
        session.add(admin)
        session.commit()
        session.close()
        resp.media = {"message": "Admin created"}


class AdminDetailResource:
    async def on_get(self, req, resp, admin_id):
        session = Session()
        admin = session.query(Admin).get(admin_id)
        if not admin:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Admin not found"}
        else:
            resp.media = {"id": admin.id, "login": admin.login}
        session.close()

    async def on_put(self, req, resp, admin_id):
        session = Session()
        data = await req.media
        admin = session.query(Admin).get(admin_id)
        if not admin:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Admin not found"}
        else:
            admin.login = data.get("login", admin.login)
            password = data.get("password")
            if password:
                admin.set_password(password)
            session.commit()
            resp.media = {"message": "Admin updated"}
        session.close()

    async def on_delete(self, req, resp, admin_id):
        session = Session()
        admin = session.query(Admin).get(admin_id)
        if not admin:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Admin not found"}
        else:
            session.delete(admin)
            session.commit()
            resp.media = {"message": "Admin deleted"}
        session.close()


class PageResource:
    async def on_get(self, req, resp):
        session = Session()
        pages = session.query(Page).all()
        data = [{"id": p.id, "title": p.title, "slug": p.slug} for p in pages]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        session = Session()
        data = await req.media
        title = data.get("title")
        slug = data.get("slug")
        page = Page(title=title, slug=slug)
        session.add(page)
        session.commit()
        session.close()
        resp.media = {"message": "Page created"}


class PageDetailResource:
    async def on_get(self, req, resp, slug):
        session = Session()
        page = session.query(Page).filter_by(slug=slug).first()
        if not page:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Page not found"}
        else:
            resp.media = {"id": page.id, "title": page.title, "slug": page.slug}
        session.close()

    async def on_put(self, req, resp, slug):
        session = Session()
        data = await req.media
        page = session.query(Page).filter_by(slug=slug).first()
        if not page:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Page not found"}
        else:
            page.title = data.get("title", page.title)
            page.slug = data.get("slug", page.slug)
            session.commit()
            resp.media = {"message": "Page updated"}
        session.close()

    async def on_delete(self, req, resp, slug):
        session = Session()
        page = session.query(Page).filter_by(slug=slug).first()
        if not page:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Page not found"}
        else:
            session.delete(page)
            session.commit()
            resp.media = {"message": "Page deleted"}
        session.close()


class ContentBlockResource:
    async def on_get(self, req, resp):
        session = Session()
        contentblocks = session.query(ContentBlock).all()
        data = [{
            'id': cb.id,
            'page_slug': cb.page_slug,
            'identifier': cb.identifier,
            'content': cb.content
        } for cb in contentblocks]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        session = Session()
        data = await req.get_media()
        page_id = data.get('page_id')
        identifier = data.get('identifier')
        content = data.get('content')
        contentBlock = ContentBlock(page_id=page_id, identifier=identifier, content=content)
        session.add(contentBlock)
        session.commit()
        session.close()
        resp.media = {"message": "ContentBlock created"}


class ContentBlockDetailResource:
    async def on_get(self, req, resp, identifier):
        session = Session()
        contentBlock = session.query(ContentBlock).filter_by(identifier=identifier).first()
        if not contentBlock:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'ContentBlock not found'}
        else:
            resp.media = {
                'id': contentBlock.id,
                'identifier': contentBlock.identifier,
                'content': contentBlock.content,
                'page_id': contentBlock.page_id
            }
        session.Сlose()

    async def on_put(self, req, resp, identifier):
        session = Session()
        data = await req.media
        contentBlock = session.query(ContentBlock).filter_by(identifier=identifier).first()
        if not contentBlock:
            resp.status = falcon.HTTP_404 
            resp.media = {'error': 'ContentBlock not found'}
        else:
            contentBlock.page_slug = data.get('page_slug', contentBlock.page_slug)
            contentBlock.identifier = data.get('identifier', contentBlock.identifier)
            contentBlock.content = data.get('content', contentBlock.content)
            session.commit()
            resp.media = {'message': 'ContentBlock updated'}
        session.close()

    async def on_delete(self, req, resp, identifier):
        session = Session()
        data = await req.media 
        contentBlock = session.query(ContentBlock).filter_by(identifier=identifier).first()
        if not contentBlock:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'ContentBlock not found'}
        else:
            session.delete(contentBlock)
            session.commit()
            resp.media = {'message': 'ContentBlock deleted'}
        session.close()


class ServantResource:
    async def on_get(self, req, resp):
        session = Session()
        servants = session.query(Servant).all()
        data = [{'id': s.id, 'name': s.name, 'surname': s.surname, 'email': s.email, 'phone': s.phone, 'role': s.role, 'birth_date': s.birth_date} for s in servants]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):   
        session = Session()
        data = await req.media
        name = data.get('name')
        surname = data.get('surname')
        email = data.get('email')
        phone = data.get('phone')
        role = data.get('role')
        birth_date = data.get('birth_date')
        session.add()
        session.commit()
        session.close()
        resp.media = {'message': 'Servant created'}

         
class ServantDetailResource:
    async def on_get(self, req, resp, servant_id):
        session = Session()
        servant = session.query(Servant).get(servant_id)
        if not servant:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Servant not found'}
        else:
            resp.media = {
                'id': servant.id,
                'name': servant.name,
                'surname': servant.surname,
                'email': servant.email,
                'phone': servant.phone,
                'role': servant.role,
                'birth_date': servant.birth_date
            }
        session.close() 

    async def on_put(self, req, resp, servant_id):
        session = Session()
        data = await req.media
        servant = session.query(Servant).get(servant_id)
        if not servant:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Servant not found'}
        else:
            servant.name = data.get('name', servant.name)
            servant.surname = data.get('sername', servant.surname)
            servant.email = data.get('email', servant.email)
            servant.phone = data.get('phone', servant.phone)
            servant.role = data.get('role', servant.role)
            servant.birth_date = data.get('birth_date', servant.birth_date)
            session.commit()
            resp.mdeia = {'message', 'Servant updated'}
        session.close()           

    async def on_delete(self, req, resp, servant_id):
        session = Session()
        servant = session.query(Servant).get(servant_id)
        if not servant:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'PServant not found'}
        else:
            session.delete(servant)
            session.commit()
            resp.media = {'message': 'Servant deleted'}
        session.close()      


class ParishionerResource:
    async def on_get(self, req, resp):
        session = Session()
        parishioner = session.query(Parishioner).all()
        data = [{'id': par.id, 'name': par.name, 'surname': par.surname, 'email': par.email, 'phone': par.phone, 'birth_date': par.birth_date}]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        session = Session()
        data = await req.media 
        name = data.get('name')
        surname = data.get('surname')
        email = data.get('email')
        phone = data.get('phone')
        birth_date = data.get('birth_date')
        parishioner = Parishioner(name=name, surname=surname, email=email, phone=phone, birth_date=birth_date)
        session.add(parishioner)
        session.commit()
        session.close()
        resp.media = {'message': 'Parishioner created'}


class ParishionerDetailResource:
    async def on_get(self, req, resp, parishioner_id):
        session = Session()
        parishioner = session.query(Parishioner).get(parishioner_id)
        if not parishioner:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Parishioner not found'}
        else:
            resp.media = {
                'id': parishioner.id,
                'name': parishioner.name,
                'surname': parishioner.surname,
                'email': parishioner.email,
                'phone': parishioner.birth_date
            }
        session.close()        

    async def on_put(self, req, resp, parishioner_id):
        session = Session()
        data = await req.media
        parishioner = session.query(Parishioner).get(parishioner_id)
        if not parishioner:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Parishiner not found'}
        else:
            parishioner.name = data.get('name', parishioner.name)
            parishioner.surname = data.get('surname', parishioner.surname)
            parishioner.email = data.get('email', parishioner.email)
            parishioner.phone = data.get('phone', parishioner.phone)
            parishioner.birth_date = data.get('birth_date', parishioner.birth_date)
            session.commit()
            resp.media = {'message': 'Parishioner updated'}
        session.close()        
        
    async def on_delete(self, req, resp, parishioner_id):
        session = Session()
        parishioner = session.query(Parishioner).get(parishioner_id)
        if not parishioner:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Parishioner not found'}
        else:
            session.delete(parishioner)
            session.commit()
            resp.media = {'message': 'Parishioner deleted'}
        session.close()


class ServiceResource:
    async def on_get(self, req, resp):
        session = Session()
        services = session.query(Service).all()
        data = [{'id': se.id,
                 'title': se.title,
                 'description': se.description, 
                 'identifier':  se.identifier,
                 'date': se.date,
                 'time': se.time,
                 'location': se.location,
                 'servant_id': se.servant_id,
                 'parishoner_id': se.parishioner_id
                 }
                 for se in services
                 ]
        session.close()
        resp.media = data 

    async def on_post(self, req, resp):
        session = Session()
        data = await req.media
        title = data.get('title')
        description = data.get('description')
        identifier = data.get('identifier')
        date = data.get('date')
        time = date.get('time')
        location = date.get('location')
        servant_id = date.get('servant_id')
        parishioner_id = date.get('parishioner_id')
        service = Service(title=title, description=description, date=date, time=time, location=location, servant_id=servant_id, parishioner_id=parishioner_id)
        session.add(service)
        session.commit()
        session.close()
        resp.media = {'message': 'Service created'} 

class ServiceDetailResource:
    async def on_get(self, req, resp, identifier):
        session = Session()
        service = session.query(Service).get(identifier)
        if not service:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Service not found'}
        else:
            resp.media = {
                'id': service.id,
                'title': service.title,
                'description': service.description,
                'identifier': service.identifier,
                'date': service.date,
                'time': service.time,
                'location': service.location,
                'servant_id': service.servant_id,
                'parishioner_id': service.parishioner_id
            }
        session.close()        

    async def on_put(self, req, res, identifier):
        session = Session()
        data = await req.media
        service = session.query(Service).get(identifier)
        if not service:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Servcie not found'}
        else:
            service.title = data.get('title', service.title)
            service.description = data.get('description', service.description)
            service.identifier = data.get('identifier', service.identifier)
            service.date = data.get('date', service.date)
            service.time = data.get('time', service.time)
            service.location = data.get('location', service.location)
            service.servant_id = data.get('servant id', service.servant_id)
            service.parishioner_id = data.get('parishioner id', service.parishioner_id)
            session.commit()
            resp.media = {'message': 'Service updated'}
        session.close()
          
    async def on_delete(self, req, resp, identifier):    
        session = Session()
        service = service.query(Service).get(identifier)
        if not service:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Service not found'}
        else:
            session.delete(service)
            session.commit()
            resp.media = {'message': 'Service deleted'}
        session.close()                    


class EventResource:
    async def op_get(self, req, resp):
        session = Session()
        events = session.query(Event).all()
        data = [{
            'id': ev.id,
            'identifier': ev.identifier,
            'title': ev.title, 
            'description': ev.description, 
            'date': ev.date, 
            'time': ev.time,
            'location': ev.location, 
            'servant_id': ev.servant_id, 
            'parishioner_id': ev.parishioner_id
            }for ev in events]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        session = Session()
        data = await req.media
        identifier = data.get('identifier')
        title = data.get('title')
        description = data.get('description')
        date = data.get('date')
        time = data.get('time')
        location = data.get('location')
        servant_id = data.get('servant id')
        parishioner_id = data.ger('parishioner id')
        event = Event(identifier=identifier, title=title, description=description, date=date, location=location, servant_id=servant_id, parishioner_id=parishioner_id)
        session.add(event)
        session.commit()
        session.close()
        resp.media = {'message', 'Event created'}


class EventDetailResource:
    async def on_get(self, req, resp, identifier):
        session = Session()
        event = session.query(Event).get(identifier)
        if not event:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Event not found'}
        else:
            resp.media = {
                'id': event.id,
                'identifier': event.identifier,
                'title': event.title,
                'description': event.description,
                'date': event.date,
                'time': event.time, 
                'location': event.location,
                'servant_id': event.servant_id,
                'parishioner_id': event.parishioner_id
                 }    
        session.close()

    async def on_put(self, req, res, identifier):
        session = Session()
        data = await req.media
        event = session.query(Event).get(identifier)
        if not event:
            resp.status = falcon.HTTP_404
            resp.media = {'error', 'Event not found'}
        else:
            event.identifier = data.get('identifier')
            event.title = data.get('title')
            event.descrition = data.get('description')
            event.date = data.get('date')
            event.time = data.get('time')
            event.location = data.get('location')
            event.servant_id = data.get('servant id')
            event.parishioner_id = data.get('parishioner id')
            session.commit()
            resp.media = {'message': 'Event updated'}
        session.close()

    async def on_delete(self, req, resp, identifier):
        session = Session()
        event = session.query(Event).get(identifier)
        if not event:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'Event not found'}
        else:
            session.delete(event)
            session.commit()
            resp.media = {'message': 'Event deleted'}
        session.close()


class NewResorce:
    async def on_get(self, req, resp):
        session = Session()
        news = session.query(New).all()
        data = [
            {
                'id': n.id,
                'identifier': n.identifier,
                'title': n.title,
                'content': n.content,
            }
            for n in news
        ]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        session = Session()
        data = await req.media
        identifier = data.get('identifier')
        title = data.get('title')
        content = data.get('content')
        new = New(identifier=identifier, title=title, content=content)
        session.add(new)
        session.commit()
        session.close()
        resp.media = {'message': 'New created'}

class NewDetailResource:
    async def on_get(self, req, resp, identifier):
        session = Session()
        new = session.query(New).get(identifier)
        if not new:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'New not found'}
        else:
            resp.media = {
                'id': new.id,
                'identifier': new.identifier,
                'title': new.title,
                'content': new.content
                        }  
        session.close()                

    async def on_put(self, req, resp, identifier):
        session = Session()
        data = await req.media
        new = session.query(New).get(identifier)
        if not new:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'New not found'}
        else:
            new.identifier = data.get('identifier', new.identifier)
            new.title = data.get('title', new.title)
            new.content = data.get('content', new.content)
            session.commit()
            resp.media = {'message': 'New updated'}
        session.close()        

    async def on_delete(self, req, resp, identifier):
        session = Session()
        new = session.query(New).get(identifier)
        if not new:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'New not found'}
        else:
            session.delete(new)
            session.commit()
            resp.media = {'message': 'New deleted'}
        session.close()        


class PostResource:
    async def on_get(self, req, resp):
        session = Session()
        posts = session.query(Post).all()
        data = [{'id': po.id, 'title': po.title, 'content': po.content}for po in posts]
        session.close()
        resp.media = data

    async def on_post(self, req, resp):
        pass

class PostDetailResource:
    async def on_get(self, req, resp, post_id):
        pass

    async def on_put(self, req, resp, post_id):
        pass

    async def on_delete(self, req, resp, post_id):
        pass    

# DB init
Base.metadata.create_all(engine)

# Routes
app.add_route("/home", HomeResource())
app.add_route("/admins", AdminResource())
app.add_route("/admins/{admin_id:int}", AdminDetailResource())
app.add_route("/pages", PageResource())
app.add_route("/pages/{slug}", PageDetailResource())
app.add_route("/content_blocks", ContentBlockResource())
app.add_route("/content_blocks/{identifier}", ContentBlockDetailResource())
app.add_route("/servants", ServantResource())
app.add_route("/servants/{servant_id:id}", ServantDetailResource())
app.add_route("/parishioners", ParishionerResource())
app.add_route("/parishioners/{parishioner_id:id}", ParishionerDetailResource())
app.add_route("/services/", ServiceResource())
app.add_route("/services/{identifier}", ServiceDetailResource())
app.add_route("/events", EventResource())
app.add_route("/events/{identifier}", EventDetailResource())
app.add_route("/news", NewResorce())
app.add_route("/news/{identifier}", NewDetailResource())
app.add_route("/posts", PostResource())
app.add_route("/posts/{post_id:id}", PostDetailResource())
