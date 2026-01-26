// API helper with bearer token
window.apiFetch = (url, options = {}) => {
  const token = localStorage.getItem("auth_token");
  const headers = Object.assign({}, options.headers || {});
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(url, Object.assign({}, options, { headers }));
};
