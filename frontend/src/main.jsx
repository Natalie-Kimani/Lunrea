import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import InstallPrompt from "./InstallPrompt.jsx";
import "./styles.css";
import { registerSW } from "virtual:pwa-register";

registerSW({ immediate: true });

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
    <InstallPrompt />
  </React.StrictMode>
);
