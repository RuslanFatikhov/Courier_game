// static/js/socket.js

// Создаем глобальное подключение Socket.IO
const token = localStorage.getItem("auth_token");
window.__socket = io({
  transports: ["polling"],
  query: token ? { token } : {}
});

// Логируем соединение
window.__socket.on("connect", () => {
  console.log("✅ Socket.IO connected:", window.__socket.id);
});

window.__socket.on("disconnect", () => {
  console.log("❌ Socket.IO disconnected");
});
