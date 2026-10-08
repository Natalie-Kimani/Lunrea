import { useEffect, useState } from "react";

// Small floating "Install Lunrea" button + offline notice.
export default function InstallPrompt() {
  const [deferred, setDeferred] = useState(null);
  const [offline, setOffline] = useState(typeof navigator !== "undefined" && !navigator.onLine);

  useEffect(() => {
    const onPrompt = (event) => { event.preventDefault(); setDeferred(event); };
    const onInstalled = () => setDeferred(null);
    const goOffline = () => setOffline(true);
    const goOnline = () => setOffline(false);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    window.addEventListener("offline", goOffline);
    window.addEventListener("online", goOnline);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
      window.removeEventListener("offline", goOffline);
      window.removeEventListener("online", goOnline);
    };
  }, []);

  async function install() {
    if (!deferred) return;
    deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  }

  const base = {
    position: "fixed", left: "50%", transform: "translateX(-50%)", zIndex: 9999,
    padding: "10px 18px", borderRadius: 999, font: "600 14px system-ui, sans-serif",
    boxShadow: "0 8px 30px rgba(0,0,0,.35)",
  };

  return (
    <>
      {offline && (
        <div role="status" style={{ ...base, top: "max(12px, env(safe-area-inset-top))", background: "#2a2631", color: "#f3e9d8", border: "1px solid #4b4358" }}>
          You're offline. Lunrea needs a connection to load your memories.
        </div>
      )}
      {deferred && (
        <button onClick={install} style={{ ...base, bottom: "max(84px, env(safe-area-inset-bottom))", background: "#e9d5b0", color: "#17151a", border: 0, cursor: "pointer" }}>
          Install Lunrea
        </button>
      )}
    </>
  );
}
