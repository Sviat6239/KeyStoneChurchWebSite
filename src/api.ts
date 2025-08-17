import { get } from "svelte/store";
import { auth } from "./auth";

const BASE_URL = "http://localhost:8000";

function getHeaders(): HeadersInit {
    const { token } = get(auth);
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
}

export async function getResource<T>(resource: string): Promise<T[]> {
    const res = await fetch(`${BASE_URL}/${resource}`, { headers: getHeaders() });
    return await res.json();
}

export async function createResource<T>(resource: string, data: T): Promise<any> {
    const res = await fetch(`${BASE_URL}/${resource}`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(data),
    });
    return await res.json();
}

export async function updateResource<T>(resource: string, id: string | number, data: T): Promise<any> {
    const res = await fetch(`${BASE_URL}/${resource}/${id}`, {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify(data),
    });
    return await res.json();
}

export async function deleteResource(resource: string, id: string | number): Promise<any> {
    const res = await fetch(`${BASE_URL}/${resource}/${id}`, {
        method: "DELETE",
        headers: getHeaders(),
    });
    return await res.json();
}

export async function loginAPI(login: string, password: string) {
    const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login, password }),
    });
    return await res.json();
}

export async function logoutAPI(token: string) {
    const res = await fetch(`${BASE_URL}/logout`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ token }),
    });
    return await res.json();
}
