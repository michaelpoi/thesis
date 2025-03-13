
export const fetchWithAuth = (url, options = {}) => {
    const token = localStorage.getItem('token');

    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
        }
    })
    .then(response => {
        if (response.status === 401) {
            window.location.href = "/login";  // Redirect to login on unauthorized
            return null;
        }
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .catch(error => {
        console.error("API Error:", error);
        throw error;  // Re-throw for handling in components
    });
};
