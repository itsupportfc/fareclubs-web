const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function signupUser({ username, email, password }) {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Signup failed");
    }

    return data;
}

export async function loginUser({ username, password }) {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Login failed");
    }

    return data;
}

export async function getCurrentUser(token) {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Unable to load profile");
    }

    return data;
}
