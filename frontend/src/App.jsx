import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";

function App() {
  const [admins, setAdmins] = useState([]);
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [editId, setEditId] = useState(null);

  // ===== Получение всех админов =====
  const fetchAdmins = async () => {
    try {
      const res = await axios.get(`${API_URL}/admins`);
      setAdmins(res.data);
    } catch (err) {
      console.error("Ошибка при получении админов:", err);
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  // ===== Создание нового админа =====
  const createAdmin = async () => {
    try {
      await axios.post(`${API_URL}/admins/create`, { login, password });
      setLogin("");
      setPassword("");
      fetchAdmins();
    } catch (err) {
      console.error("Ошибка при создании:", err);
    }
  };

  // ===== Редактирование админа =====
  const updateAdmin = async (id) => {
    try {
      await axios.put(`${API_URL}/admins/put/${id}`, { login, password });
      setLogin("");
      setPassword("");
      setEditId(null);
      fetchAdmins();
    } catch (err) {
      console.error("Ошибка при обновлении:", err);
    }
  };

  // ===== Удаление админа =====
  const deleteAdmin = async (id) => {
    try {
      await axios.delete(`${API_URL}/admins/delete/${id}`);
      fetchAdmins();
    } catch (err) {
      console.error("Ошибка при удалении:", err);
    }
  };

  return (
    <div style={{ margin: "2rem" }}>
      <h1>Админы</h1>

      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Логин"
          value={login}
          onChange={(e) => setLogin(e.target.value)}
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {editId ? (
          <button onClick={() => updateAdmin(editId)}>Обновить</button>
        ) : (
          <button onClick={createAdmin}>Создать</button>
        )}
        {editId && <button onClick={() => setEditId(null)}>Отмена</button>}
      </div>

      <ul>
        {admins.map((admin) => (
          <li key={admin.id}>
            {admin.login}{" "}
            <button
              onClick={() => {
                setLogin(admin.login);
                setPassword("");
                setEditId(admin.id);
              }}
            >
              Редактировать
            </button>
            <button onClick={() => deleteAdmin(admin.id)}>Удалить</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
