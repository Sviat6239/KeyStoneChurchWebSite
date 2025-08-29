import express from 'express';
import bodyParser from 'body-parser';
import mongoose from 'mongoose';
import jwt from "jsonwebtoken";
import bcrypt from 'bcrypt';
import cors from 'cors';

const app = express();
app.use(bodyParser.json());

// ===== CORS =====
app.use(cors({
    origin: "http://localhost:5173",
    methods: ["GET", "POST", "PUT", "DELETE"],
    credentials: true
}));

const port = 8000;

const SECRET = "supersecretkey";

// ===== MongoDB Connection =====
mongoose.connect('mongodb://localhost:27017/church', {
    useNewUrlParser: true,
    useUnifiedTopology: true,
});
const db = mongoose.connection;
db.on('error', console.error.bind(console, 'MongoDB connection error:'));
db.once('open', () => console.log('MongoDB connected!'));

// ===== Schemas and Models =====

// Admin
const adminSchema = new mongoose.Schema({
    login: { type: String, required: true, unique: true, maxlength: 50 },
    password: { type: String, required: true, maxlength: 255 },
}, { timestamps: true });

adminSchema.methods.setPassword = async function (password) {
    this.password = await bcrypt.hash(password, 10);
};

adminSchema.methods.checkPassword = async function (password) {
    return await bcrypt.compare(password, this.password);
};

const Admin = mongoose.model('Admin', adminSchema);

// Page
const pageSchema = new mongoose.Schema({
    title: { type: String, required: true, maxlength: 255 },
    slug: { type: String, required: true, unique: true, maxlength: 255 },
}, { timestamps: true });

const Page = mongoose.model('Page', pageSchema);

// ContentBlock
const contentBlockSchema = new mongoose.Schema({
    pageSlug: { type: String, required: true },
    identifier: { type: String, required: true, maxlength: 255 },
    content: { type: String, required: true },
}, { timestamps: true });

const ContentBlock = mongoose.model('ContentBlock', contentBlockSchema);

// Servant
const servantSchema = new mongoose.Schema({
    name: { type: String, required: true, maxlength: 255 },
    surname: { type: String, required: true, maxlength: 255 },
    role: { type: String },
}, { timestamps: true });

const Servant = mongoose.model('Servant', servantSchema);

// Service
const serviceSchema = new mongoose.Schema({
    title: { type: String, required: true, maxlength: 255 },
    description: { type: String, required: true },
    identifier: { type: String, required: true, unique: true },
    date: { type: Date, required: true },
    time: { type: String, required: true },
    location: { type: String, required: true, maxlength: 255 },
    servantId: { type: mongoose.Schema.Types.ObjectId, ref: 'Servant', required: true },
}, { timestamps: true });

const Service = mongoose.model('Service', serviceSchema);

// Event
const eventSchema = new mongoose.Schema({
    identifier: { type: String, required: true, unique: true },
    title: { type: String, required: true, maxlength: 255 },
    description: { type: String, required: true },
    date: { type: Date, required: true },
    time: { type: String },
    location: { type: String, required: true, maxlength: 255 },
    servantId: { type: mongoose.Schema.Types.ObjectId, ref: 'Servant', required: true },
}, { timestamps: true });

const Event = mongoose.model('Event', eventSchema);

// News
const newsSchema = new mongoose.Schema({
    identifier: { type: String, required: true, unique: true },
    title: { type: String, required: true, maxlength: 320 },
    content: { type: String, required: true },
}, { timestamps: true });

const New = mongoose.model('New', newsSchema);

// Post
const postSchema = new mongoose.Schema({
    title: { type: String, required: true, maxlength: 320 },
    content: { type: String, required: true },
}, { timestamps: true });

const Post = mongoose.model('Post', postSchema);

// Need
const needSchema = new mongoose.Schema({
    token: { type: String, required: true },
    title: { type: String, required: true, maxlength: 400 },
    content: { type: String, required: true },
    email: { type: String, required: true, maxlength: 60 },
    phone: { type: String, maxlength: 15 },
    name: { type: String, required: true, maxlength: 120 },
    surname: { type: String, required: true, maxlength: 120 },
}, { timestamps: true });

const Need = mongoose.model('Need', needSchema);


// ===== AuthMiddleware =====
function authMiddleware(req, res, next) {
    const authHeader = req.headers['authorization'];
    if (!authHeader) return res.status(401).json({ message: "No token provided" });

    const token = authHeader.split(' ')[1];
    try {
        const decoded = jwt.verify(token, SECRET);
        req.user = decoded;
        next();
    } catch (err) {
        res.status(403).json({ message: "Invalid token" });
    }
}

function adminOnly(req, res, next) {
    if (!req.user || req.user.role !== 'admin') {
        return res.status(403).json({ message: "Admins only" });
    }
    next();
}

// ===== Async Handler =====
function asyncHandler(fn) {
    return (req, res, next) => {
        Promise.resolve(fn(req, res, next)).catch(next);
    };
}
// ===== Routes =====
app.post('/login', asyncHandler(async (req, res) => {
    const { login, password } = req.body;
    if (!login || !password) return res.status(400).json({ message: 'Login and password required' });

    const admin = await Admin.findOne({ login });
    if (!admin) return res.status(404).json({ message: 'Admin not found' });

    const valid = await admin.checkPassword(password);
    if (!valid) return res.status(401).json({ message: 'Wrong password' });

    const token = jwt.sign(
        { id: admin._id.toString(), login: admin.login, role: 'admin' },
        SECRET,
        { expiresIn: '1h' }
    );

    res.json({ token });
}));


app.get('/adminpanel', asyncHandler(async (req, res) => {

}));

// ===== Admin CRUD =====
app.get('/admins', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const admins = await Admin.find({}, '_id login').lean();
    res.json(admins.map(a => ({ id: a._id.toString(), login: a.login })));
}));

app.get('/admins/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const admin = await Admin.findById(req.params.id, '_id login').lean();
    if (!admin) return res.status(404).json({ message: 'Admin not found' });
    res.json({ id: admin._id.toString(), login: admin.login });
}));

app.post('/admins/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { login, password } = req.body;
    if (!login || !password) return res.status(400).json({ message: 'Login and password required!' });

    const admin = new Admin({ login });
    await admin.setPassword(password);
    await admin.save();

    res.status(201).json({ id: admin._id.toString(), login: admin.login });
}));

app.put('/admins/put/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { login, password } = req.body;
    const admin = await Admin.findById(req.params.id);
    if (!admin) return res.status(404).json({ message: 'Admin not found!' });

    if (login) admin.login = login;
    if (password) await admin.setPassword(password);

    await admin.save();
    res.json({ id: admin._id.toString(), login: admin.login });
}));

app.delete('/admins/delete/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const admin = await Admin.findById(req.params.id);
    if (!admin) return res.status(404).json({ message: 'Admin not found' });

    await admin.deleteOne();
    res.json({ message: 'Admin deleted' });
}));

// ===== Page CRUD =====
app.get('/pages', asyncHandler(async (req, res) => {
    const pages = await Page.find({}, 'title slug').lean();
    const result = pages.map(p => ({
        id: p._id.toString(),
        title: p.title,
        slug: p.slug
    }));
    res.json(result);
}));

app.get('/pages/:slug', asyncHandler(async (req, res) => {
    const page = await Page.findOne({ slug: req.params.slug }, 'title slug').lean();
    if (!page) return res.status(404).json({ message: 'Page not found' });
    res.json({
        id: page._id.toString(),
        title: page.title,
        slug: page.slug
    });
}));

app.post('/pages/create', asyncHandler(async (req, res) => {
    const { title, slug } = req.body;
    if (!title || !slug) return res.status(400).json({ message: 'Title and slug required' });

    const page = new Page({ title, slug });
    await page.save();

    res.status(201).json({
        id: page._id.toString(),
        title: page.title,
        slug: page.slug
    });
}));

app.put('/pages/put/:slug', asyncHandler(async (req, res) => {
    const { title, slug } = req.body;
    const page = await Page.findOne({ slug: req.params.slug });
    if (!page) return res.status(404).json({ message: 'Page not found' });

    if (title) page.title = title;
    if (slug) page.slug = slug;

    await page.save();
    res.json({
        id: page._id.toString(),
        title: page.title,
        slug: page.slug
    });
}));

app.delete('/pages/delete/:slug', asyncHandler(async (req, res) => {
    const page = await Page.findOne({ slug: req.params.slug });
    if (!page) return res.status(404).json({ message: 'Page not found' });

    await page.deleteOne();
    res.json({ message: 'Page deleted' });
}));

// ===== Content Block CRUD =====
app.get('/cntblocks', asyncHandler(async (req, res) => {
    const cntblocks = await ContentBlock.find({}, 'pageSlug identifier content').lean();
    const result = cntblocks.map(cntb => ({
        id: cntb._id.toString(),
        pageSlug: cntb.pageSlug,
        identifier: cntb.identifier,
        content: cntb.content
    }));
    res.json(result);
}));

app.get('/cntblocks/:identifier', asyncHandler(async (req, res) => {
    const cntblock = await ContentBlock.findOne({ pageSlug: req.params.pageSlug }, 'pageSlug identifier content').lean();
    if (!cntblock) return res.status(404).json({ message: 'ContentBlock not found' });
    res.json({
        id: cntblock._id.toString(),
        pageSlug: cntblock.pageSlug,
        identifier: cntblock.identifier,
        content: cntblock.content
    });
}));

app.post('/cntblocks/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { pageSlug, identifier, content } = req.body;
    if (!pageSlug || !identifier || !content) return res.status(400).json({ message: 'PageSlug, identifier and content required' });

    const cntblock = new ContentBlock({ pageSlug, identifier, content });
    await cntblock.save();

    res.status(201).json({
        id: cntblock._id.toString(),
        pageSlug: cntblock.pageSlug,
        identifier: cntblock.identifier,
        content: cntblock.content
    });
}));

app.put('/cntblocks/put/:identifier', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { pageSlug, identifier, content } = req.body;
    const cntblock = await ContentBlock.findOne({ pageSlug: req.params.pageSLug });
    if (!cntblock) return res.status(404).json({ message: 'ContentBlock not found' });

    if (pageSlug) cntblock.pageSlug = pageSlug;
    if (identifier) cntblock.identifier = identifier;
    if (content) cntblock.content = content;

    await cntblock.save();
    res.json({
        id: cntblock._id.toString(),
        pageSlug: cntblock.pageSlug,
        identifier: cntblock.identifier,
        content: cntblock.content
    });
}));

app.delete('/cntblock/delete/:identifier', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const cntblock = await ContentBlock.findOne({ identifier: req.params.identifier });
    if (!cntblock) return res.status(404).json({ message: 'ContentBlock not found' });

    await cntblock.deleteOne();
    res.json({ message: 'ContentBlock deleted' });
}));

// ===== Servant CRUD =====
app.get('/servants', asyncHandler(async (req, res) => {
    const sevants = await Servant.find({}, 'name surname role').lean();
    const result = servantSchema.map(srv => ({ id: srv._id.toString(), name: srv.name, surname: srv.surname, role: srv.role }));
    res.json(result);
}));

app.get('/servants/:id', asyncHandler(async (req, res) => {
    const servant = await Servant.findById({ id: req.params.id }, '_id name surname email phone role birthDate').lean();
    if (!servant) return res.status(404).json({ message: 'Servant not found' });
    res.json({
        id: servant._id.toString(),
        name: servant.name,
        surname: servant.surname,
        role: servant.role
    });
}));

app.post('/servants/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { name, surname, role, } = req.body;
    if (!name || !surname || !role) return res.status(400).json({ message: 'Name, surname and role are required' });

    const servant = new Servant({ name, surname, role });
    await servant.save();

    res.status(201).json({
        id: servant._id.toString(),
        name: servant.name,
        surname: servant.surname,
        role: servant.role
    });
}));

app.put('/servants/put/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { name, surname, role } = req.body;
    const servant = await Servant.findById({ id: req.params.id }, '_id name surname role').lean();
    if (!servant) return res.status(404).json({ message: 'Servant not found' });

    if (name) servant.name = name;
    if (surname) servant.surname = surname;
    if (role) servant.role = role;

    await servant.save()
    res.json({
        id: servant._id.toString(),
        name: servant.name,
        surname: servant.surname,
        role: servant.role
    });
}));

app.delete('/servants/delete/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const servant = await Servant.findById({ id: req.params.id });
    if (!servant) return res.status(404).json({ message: 'Servant not found' });

    await servant.deleteOne();
    res.json({ message: 'Servant delted' });
}));

// ===== Service CRUD =====
app.get('/services', asyncHandler(async (req, res) => {
    const services = await Service.find({}, 'title description identifier date time location servantId').lean();
    const result = services.map(service => ({
        id: service._id.toString(),
        title: service.title,
        description: service.description,
        identifier: service.identifier,
        date: service.date,
        time: service.time,
        location: service.location,
        servantId: service.servantId
    }));
    res.json(result);
}));

app.get('/services/:id', asyncHandler(async (req, res) => {
    const service = await Service.findById({ id: req.params.id }, 'title description identifier date time location servantId');
    if (!service) return res.status(404).json({ message: 'Service not found' });
    res.json({
        id: service._id.toString,
        title: service.title,
        description: service.description,
        identifier: service.identifier,
        date: service.date,
        time: service.time,
        location: service.location,
        servantId: service.servantId
    });
}));

app.post('/services/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { title, description, identifier, date, time, location, servantId } = req.body;
    if (!title || !description || !identifier || !date || !time || !location || !servantId) {
        return res.status(404).json({ message: 'Title, description, identifier, date, time, location and servantId are required' });
    };

    const service = new Sevice({ title, description, identifier, date, time, location, servantId });
    await service.save();

    res.status(201).json({
        id: service._id.toString(),
        title: service.title,
        description: service.description,
        identifier: service.identifier,
        date: service.date,
        time: service.time,
        location: service.location,
        servantId: service.servantId
    });
}));

app.put('/services/put/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { title, description, identifier, date, time, location, servantId } = req.body;
    const service = await Service.findById({ id: req.params.id });
    if (!service) return res.status(404).json({ message: 'Service not found' });

    if (title) service.title = title;
    if (description) service.description = description;
    if (identifier) service.identifier = identifier;
    if (date) service.date = date;
    if (time) service.time = time;
    if (location) service.location = location;
    if (servantId) service.servantId = servantId;

    await service.save();
    res.json({
        id: service._id.toString(),
        title: service.title,
        description: service.description,
        identifier: service.identifier,
        date: service.date,
        time: service.time,
        location: service.location,
        servantId: service.servantId
    });
}));

app.delete('/services/delete/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const service = await Service.findById({ id: req.param.id });
    if (!service) return res.status(404).json({ message: 'Service not found' });

    await service.deleteOne();
    res.json({ message: 'Service deleted' });
}));

// ===== Event CRUD =====
app.get('/events', asyncHandler(async (req, res) => {
    const events = await Event.find({}, '_id identifier title description date time location servantId').lean();
    res.json(events.map(event => ({
        id: event._id.toString(),
        identifier: event.identifier,
        title: event.title,
        description: event.description,
        date: event.date,
        time: event.time,
        location: event.location,
        servantId: event.servantId
    })));
}));

app.get('/events/:id', asyncHandler(async (req, res) => {
    const event = await Event.findById({ id: req.params.id }, '_id identifier title description date time location servantId').lean();
    if (!event) return res.status(404).json({ message: 'Event not found' });
    res.json({
        id: event._id.toString(),
        identifier: event.identifier,
        title: event.title,
        description: event.description,
        date: event.date,
        time: event.time,
        location: event.location,
        servantId: event.servantId
    });
}));

app.post('/events/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { identifier, title, description, date, time, location, servantId } = req.body;
    if (!identifier || !title || !description || !date || !time || !location || !servantId) return res.status(400).json({
        message: 'Identifier, title, description, date, time, location and servantId are required'
    });

    const event = new Event({ identifier, title, description, date, time, location, servantId });
    await event.save();

    res.status(201).json({
        id: event._id.toString(),
        title: event.title,
        description: event.description,
        date: event.date,
        time: event.time,
        location: event.location,
        servantId: event.servantId
    });
}));

app.put('/events/put/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { identifier, title, description, date, time, location, servantId } = req.body;
    const event = await Event.findById({ id: req.params.id });
    if (!event) return res.status(404).json({ message: 'Event not found' });

    if (identifier) event.identifier = identifier;
    if (title) event.title = title;
    if (description) event.description = description;
    if (date) event.date = date;
    if (time) event.time = time;
    if (location) event.location = location;
    if (servantId) event.servantId = servantId;

    await event.save();
    res.json({
        id: event._id.toString(),
        title: event.title,
        description: event.description,
        date: event.date,
        time: event.time,
        location: event.location,
        servantId: event.servantId
    });
}));

app.delete('/events/delete/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const event = await Event.findById({ id: req.params.id });
    if (!event) return res.status(404).json({ message: 'Event not found' });

    await event.deleteOne();
    res.json({ message: 'Event deleted' });
}));

// ===== News CRUD =====
app.get('/news', asyncHandler(async (req, res) => {
    const news = await New.find({}, 'identifier title content').lean();
    const result = news.map(n => ({
        id: n._id.toString(),
        identifier: n.identifier,
        content: n.content
    }));
    res.json(result);
}));

app.get('/news/:id', asyncHandler(async (req, res) => {
    const news = await New.findById({ id: req.params.id }, 'identifier title content');
    if (!news) return res.status(404).json({ message: 'News not found' });
    res.json({
        id: news._id.tiString(),
        identifier: news.identifier,
        title: news.title,
        content: news.content
    });
}));

app.post('/news/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { identifier, title, content } = req.body;
    if (!identifier || !title || !content) return res.status(400).json({ message: 'Identifier, title and content are required' });

    const news = new New({ identifier, title, content });
    await news.save();

    res.status(201).json({
        id: news._id.toString(),
        identifier: news.identifier,
        title: news.title,
        content: news.content
    });
}));

app.put('/news/put/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { identifier, title, slug } = req.body;
    const news = await New.findById({ id: req.params.id });
    if (!news) return res.status(404).json({ message: 'News not found' });

    if (identifier) news.identifier = identifier;
    if (title) news.title = title;
    if (content) news.content = content;

    await news.save();
    res.json({
        id: news._id.toString(),
        identifier: news.identifier,
        title: news.title,
        content: news.content
    });
}));

app.delete('/news/delete/:id', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const news = await New.findById({ id: req.params.id });
    if (!news) return res.status(404).json({ message: 'News not found' });

    await news.deleteOne();
    res.json({ message: 'News deleted' });
}));

// ===== Post CRUD =====
app.get('/posts', asyncHandler(async (req, res) => {
    const posts = await Post.find({}, 'title content').lean();
    const result = posts.map(posts => ({
        id: posts._id.toString(),
        title: posts.title,
        content: posts.content
    }));
}));

app.get('/posts/:id', asyncHandler(async (req, res) => {
    const post = await Post.findById({ id: req.params.id }, 'title content').lean();
    if (!post) return res.status(404).json({ message: 'Post not found' });
    res.json({
        id: post._id.toString(),
        title: post.title,
        content: post.content
    });
}));

app.post('/posts/create', authMiddleware, adminOnly, asyncHandler(async (req, res) => {
    const { title, content } = req.body;
    if (!title || !content) return res.status(400).json({ message: 'Titile and content are required' });

    const post = new Post({ title, content });
    await post.save();

    res.status(201).json({
        id: post._id.toString(),
        title: post.title,
        content: post.content
    });
}));



// ===== Error Handling =====
app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ message: 'Internal server error', error: err.message });
});

// ===== Start Server =====
app.listen(port, () => console.log(`Server running on http://localhost:${port}`));
