import { writable } from "svelte/store";

export type UserRole = "guest" | "admin";

interface Auth {
    role: UserRole;
    token?: string;
}

export const auth = writable<Auth>({ role: "guest" });

export function login(token: string) {
    auth.set({ role: "admin", token });
    localStorage.setItem("token", token);
}

export function logout() {
    auth.set({ role: "guest" });
    localStorage.removeItem("token");
}

export function loadToken() {
    const token = localStorage.getItem("token");
    if (token) login(token);
}
