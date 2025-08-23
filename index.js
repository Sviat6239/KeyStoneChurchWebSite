import express from 'express';
import bodyParser from 'body-parser';
import { Sequelize, DataTypes, Model } from 'sequelize';
import bcrypt from 'bcrypt';

const sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: 'database.sqlite',
    logging: false,
});

const app = express();
app.use(bodyParser.json());
const port = 8000

// Admin
class Admin extends Model {
    async setPassword(password) {
        const hash = await bcrypt.hash(password, 10);
        this.password = hash;
    }

    async checkPassword(password) {
        return await bcrypt.compare(password, this.password);
    }
}

Admin.init({
    login: { type: DataTypes.STRING(50), allowNull: false, unique: true },
    password: { type: DataTypes.STRING(255), allowNull: false },
}, {
    sequelize,
    modelName: 'Admin',
    tableName: 'admins',
});

// Page
class Page extends Model { }
Page.init({
    title: { type: DataTypes.STRING(255), allowNull: false },
    slug: { type: DataTypes.STRING(255), allowNull: false, unique: true },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Page', tableName: 'pages' });

// ContentBlock
class ContentBlock extends Model { }
ContentBlock.init({
    pageSlug: { type: DataTypes.STRING, allowNull: false, references: { model: 'pages', key: 'slug' }, onDelete: 'CASCADE' },
    identifier: { type: DataTypes.STRING(255), allowNull: false },
    content: { type: DataTypes.TEXT, allowNull: false },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'ContentBlock', tableName: 'content_blocks' });

// Servant
class Servant extends Model { }
Servant.init({
    name: { type: DataTypes.STRING(255), allowNull: false },
    surname: { type: DataTypes.STRING(255), allowNull: false },
    email: { type: DataTypes.STRING(255), unique: true },
    phone: { type: DataTypes.STRING(50), unique: true },
    role: { type: DataTypes.TEXT },
    birthDate: { type: DataTypes.DATEONLY },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Servant', tableName: 'servants' });

// Parishioner
class Parishioner extends Model { }
Parishioner.init({
    name: { type: DataTypes.STRING(255), allowNull: false },
    surname: { type: DataTypes.STRING(255), allowNull: false },
    email: { type: DataTypes.STRING(255), unique: true },
    phone: { type: DataTypes.STRING(50), unique: true },
    birthDate: { type: DataTypes.DATEONLY },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Parishioner', tableName: 'parishioners' });

// Service
class Service extends Model { }
Service.init({
    title: { type: DataTypes.STRING(255), allowNull: false },
    description: { type: DataTypes.TEXT, allowNull: false },
    identifier: { type: DataTypes.STRING(255), allowNull: false, unique: true },
    date: { type: DataTypes.DATEONLY, allowNull: false },
    time: { type: DataTypes.TIME, allowNull: false },
    location: { type: DataTypes.STRING(255), allowNull: false },
    servantId: { type: DataTypes.INTEGER, allowNull: false, references: { model: Servant, key: 'id' }, onDelete: 'CASCADE' },
    parishionerId: { type: DataTypes.INTEGER, allowNull: false, references: { model: Parishioner, key: 'id' }, onDelete: 'CASCADE' },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Service', tableName: 'services' });

// Event
class Event extends Model { }
Event.init({
    identifier: { type: DataTypes.STRING(255), allowNull: false, unique: true },
    title: { type: DataTypes.STRING(255), allowNull: false },
    description: { type: DataTypes.TEXT, allowNull: false },
    date: { type: DataTypes.DATEONLY, allowNull: false },
    time: { type: DataTypes.TIME },
    location: { type: DataTypes.STRING(255), allowNull: false },
    servantId: { type: DataTypes.INTEGER, allowNull: false, references: { model: Servant, key: 'id' }, onDelete: 'CASCADE' },
    parishionerId: { type: DataTypes.INTEGER, allowNull: false, references: { model: Parishioner, key: 'id' }, onDelete: 'CASCADE' },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Event', tableName: 'events' });

// News
class New extends Model { }
New.init({
    identifier: { type: DataTypes.STRING(255), allowNull: false, unique: true },
    title: { type: DataTypes.STRING(320), allowNull: false },
    content: { type: DataTypes.TEXT, allowNull: false },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'New', tableName: 'news' });

// Post
class Post extends Model { }
Post.init({
    title: { type: DataTypes.STRING(320), allowNull: false },
    content: { type: DataTypes.TEXT, allowNull: false },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Post', tableName: 'posts' });

// Need
class Need extends Model { }
Need.init({
    token: { type: DataTypes.STRING, allowNull: false },
    title: { type: DataTypes.STRING(400), allowNull: false },
    content: { type: DataTypes.TEXT, allowNull: false },
    email: { type: DataTypes.STRING(60), allowNull: false },
    phone: { type: DataTypes.STRING(15) },
    name: { type: DataTypes.STRING(120), allowNull: false },
    surname: { type: DataTypes.STRING(120), allowNull: false },
    createdAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
    updatedAt: { type: DataTypes.DATE, defaultValue: Sequelize.NOW },
}, { sequelize, modelName: 'Need', tableName: 'needs' });

function asyncHandler(fn) {
    return (req, res, next) => {
        Promise.resolve(fn(req, res, next)).catch(next);
    };
};

app.get('/admins', asyncHandler(async (req, res) => {
    const admins = await Admin.findAll({ attributes: ['id', 'login'] });
    res.json(admins);
}));

app.get('/admins/:id', asyncHandler(async (req, res) => {
    const admin = await Admin.findByPk(req.params.id, { attributes: ['id', 'login'] });
    if (!admin) return res.status(404).json({ message: 'Admin not found' });
    res.json(admin);
}));

app.post('/admins/create', asyncHandler(async (req, res) => {
    const { login, password } = req.body;
    if (!login || !password) return res.status(400).json({ message: 'Login and password required!' });

    const admin = Admin.build({ login });
    await admin.setPassword(password);
    await admin.save();

    res.status(201).json({ id: admin.id, login: admin.login });
}));

app.put('/admins/put/:id', asyncHandler(async (req, res) => {
    const { login, password } = req.body;
    const admin = await Admin.findByPk(req.params.id);
    if (!admin) return res.status(404).json({ message: 'Admin not found!' });

    if (login) admin.login = login;
    if (password) await admin.setPassword(password);

    await admin.save();
    res.json({ id: admin.id, login: admin.login });
}));

app.delete('/admins/delete/:id', asyncHandler(async (req, res) => {
    const admin = await Admin.findByPk(req.params.id);
    if (!admin) return res.status(404).json({ message: 'Admin not found' });

    await admin.destroy();
    res.json({ message: 'Admin deleted' });
}));

app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ message: 'Internal server error', error: err.message });
});

(async () => {
    await sequelize.sync({ alter: true });
    console.log('Database synced!');
    app.listen(port, () => console.log(`Server running on http://localhost:${port}`));
})();