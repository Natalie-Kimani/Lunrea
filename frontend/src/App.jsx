import { useEffect, useMemo, useRef, useState } from "react";
import {
  api,
  clearAuth,
  downloadMedia,
  getStoredAuth,
  setAuth,
  uploadMedia,
} from "./api";

const emptyMemory = {
  title: "",
  caption: "",
  description: "",
  memory_date: "",
  location: "",
  why_it_matters: "",
};

function formatDate(value) {
  if (!value) return "No date";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function Shell({ user, onLogout, children }) {
  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <div className="brand">lunrea</div>
          <div className="tagline">where every moment can have more than one story.</div>
        </div>
        <div className="top-actions">
          <span className="user-pill">{user.display_name}</span>
          <button className="ghost" onClick={onLogout}>Lock</button>
        </div>
      </header>
      {children}
    </div>
  );
}

function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", display_name: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const data = await api(path, { method: "POST", body: JSON.stringify(form) });
      if (mode === "login") onLogin(data.access_token, data.user);
      else setMode("login");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="brand large">lunrea</div>
        <p className="lead">Your memories can hold more than one story.</p>
        <div className="tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Log in</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Create account</button>
        </div>
        <form onSubmit={submit} className="stack">
          {mode === "register" && <input placeholder="Display name" value={form.display_name} onChange={e => setForm({...form, display_name: e.target.value})} />}
          <input placeholder="Username" autoComplete="username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
          {mode === "register" && <input placeholder="Email" type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} />}
          <input placeholder="Password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
          {error && <div className="error">{error}</div>}
          <button className="primary" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Enter Lunrea" : "Create Lunrea"}</button>
        </form>
      </div>
    </main>
  );
}

function Unlock({ onUnlock, onLogout }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api("/api/auth/unlock", { method: "POST", body: JSON.stringify({ password }) });
      localStorage.setItem("lunrea_session", data.session_token);
      onUnlock();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card lock-card">
        <div className="lock-symbol">⌁</div>
        <h1>Lunrea is locked</h1>
        <p>Re-enter your password to return to your memories.</p>
        <form onSubmit={submit} className="stack">
          <input autoFocus type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
          {error && <div className="error">{error}</div>}
          <button className="primary" disabled={busy}>{busy ? "Unlocking…" : "Unlock"}</button>
          <button type="button" className="ghost wide" onClick={onLogout}>Log out</button>
        </form>
      </div>
    </main>
  );
}

function Dashboard({ user, onLogout }) {
  const [tab, setTab] = useState("memories");
  const [memories, setMemories] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    setError("");
    try {
      const [memoryData, albumData, chatData] = await Promise.all([
        api("/api/memories/"),
        api("/api/albums/"),
        api("/api/chat/rooms"),
      ]);
      setMemories(memoryData.memories || []);
      setAlbums(albumData.albums || []);
      setRooms(chatData.rooms || []);
    } catch (err) {
      if (err.status === 423) setNotice("Lunrea is locked. Refresh and unlock again.");
      else setError(err.message);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function logout() {
    try { await api("/api/auth/logout", { method: "POST" }); } catch (_) {}
    clearAuth();
    onLogout();
  }

  return (
    <Shell user={user} onLogout={logout}>
      <nav className="nav">
        {[["memories", "Memories"], ["camera", "Camera"], ["albums", "Albums"], ["chat", "Chat"]].map(([key, label]) => (
          <button key={key} className={tab === key ? "nav-active" : ""} onClick={() => { setTab(key); setSelectedRoom(null); }}>{label}</button>
        ))}
      </nav>
      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error page-error">{error}</div>}
      {tab === "memories" && <Memories memories={memories} onRefresh={refresh} />}
      {tab === "camera" && <Camera onSaved={() => { setNotice("Captured memory saved."); refresh(); setTab("memories"); }} />}
      {tab === "albums" && <Albums albums={albums} onRefresh={refresh} />}
      {tab === "chat" && <Chat user={user} rooms={rooms} selectedRoom={selectedRoom} setSelectedRoom={setSelectedRoom} onRefresh={refresh} />}
    </Shell>
  );
}

function Memories({ memories, onRefresh }) {
  const [form, setForm] = useState(emptyMemory);
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function create(event) {
    event.preventDefault();
    setSaving(true); setError("");
    try {
      const data = await api("/api/memories/", { method: "POST", body: JSON.stringify(form) });
      if (file) await uploadMedia(data.memory.id, file);
      setForm(emptyMemory); setFile(null); event.target.reset();
      await onRefresh();
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }

  return (
    <section className="content-grid">
      <div className="panel">
        <div className="section-heading"><span>New memory</span><small>everything can be optional</small></div>
        <form onSubmit={create} className="stack">
          <input placeholder="Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
          <input type="datetime-local" value={form.memory_date} onChange={e => setForm({...form, memory_date: e.target.value})} />
          <input placeholder="Location" value={form.location} onChange={e => setForm({...form, location: e.target.value})} />
          <textarea placeholder="Caption" value={form.caption} onChange={e => setForm({...form, caption: e.target.value})} />
          <textarea placeholder="Why this matters" value={form.why_it_matters} onChange={e => setForm({...form, why_it_matters: e.target.value})} />
          <textarea placeholder="Description / what you remember" value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
          <label className="file-input">Attach a photo, video or voice note<input type="file" accept="image/*,video/*,audio/*" onChange={e => setFile(e.target.files?.[0] || null)} /></label>
          {file && <div className="file-name">{file.name}</div>}
          {error && <div className="error">{error}</div>}
          <button className="primary" disabled={saving}>{saving ? "Saving…" : "Save memory"}</button>
        </form>
      </div>
      <div className="panel wide-panel">
        <div className="section-heading"><span>Your memories</span><small>{memories.length} saved</small></div>
        <div className="memory-list">
          {memories.length === 0 && <div className="empty">Your first story is waiting here.</div>}
          {memories.map(memory => <article className="memory-card" key={memory.id}>
            <div className="memory-date">{formatDate(memory.memory_date)}</div>
            <h3>{memory.title || "Untitled moment"}</h3>
            <p>{memory.caption || memory.description || "A moment waiting for its story."}</p>
            {memory.location && <span className="tag">{memory.location}</span>}
            {memory.why_it_matters && <blockquote>{memory.why_it_matters}</blockquote>}
          </article>)}
        </div>
      </div>
    </section>
  );
}

function Camera({ onSaved }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [title, setTitle] = useState("");
  const [caption, setCaption] = useState("");
  const [choice, setChoice] = useState("lunrea");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function choose(event) {
    const next = event.target.files?.[0];
    if (!next) return;
    setFile(next); setPreview(URL.createObjectURL(next));
  }

  async function save(event) {
    event.preventDefault();
    if (!file) return;
    setBusy(true); setError("");
    try {
      if (choice === "device" || choice === "both") {
        const url = URL.createObjectURL(file);
        const link = document.createElement("a");
        link.href = url; link.download = file.name; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      if (choice === "lunrea" || choice === "both") {
        const data = await api("/api/memories/", {
          method: "POST",
          body: JSON.stringify({ title, caption, memory_date: new Date().toISOString() }),
        });
        await uploadMedia(data.memory.id, file);
      }
      onSaved();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <section className="camera-page">
      <div className="panel camera-panel">
        <div className="section-heading"><span>Capture a moment</span><small>save it here, there, or both</small></div>
        {!file ? (
          <button className="camera-button" onClick={() => inputRef.current?.click()}>
            <span>⌾</span><strong>Open camera</strong><small>On mobile, this opens your camera.</small>
          </button>
        ) : (
          <form onSubmit={save} className="stack">
            <img className="preview" src={preview} alt="Capture preview" />
            <input placeholder="Give this moment a title" value={title} onChange={e => setTitle(e.target.value)} />
            <textarea placeholder="Add a caption" value={caption} onChange={e => setCaption(e.target.value)} />
            <div className="choice-grid">
              {[["lunrea", "Save to Lunrea"], ["device", "Save to device"], ["both", "Save to both"]].map(([value, label]) => (
                <label key={value} className={choice === value ? "choice selected" : "choice"}><input type="radio" name="save" value={value} checked={choice === value} onChange={e => setChoice(e.target.value)} />{label}</label>
              ))}
            </div>
            {error && <div className="error">{error}</div>}
            <div className="button-row"><button type="button" className="ghost" onClick={() => { setFile(null); setPreview(""); }}>Retake</button><button className="primary" disabled={busy}>{busy ? "Saving…" : "Keep this moment"}</button></div>
          </form>
        )}
        <input ref={inputRef} className="hidden" type="file" accept="image/*" capture="environment" onChange={choose} />
      </div>
    </section>
  );
}

function Albums({ albums, onRefresh }) {
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  async function create(event) {
    event.preventDefault(); setError("");
    try {
      await api("/api/albums/", { method: "POST", body: JSON.stringify({ title, privacy: "private" }) });
      setTitle(""); await onRefresh();
    } catch (err) { setError(err.message); }
  }

  return (
    <section className="content-grid single">
      <div className="panel">
        <div className="section-heading"><span>Story spaces</span><small>albums can become shared chapters</small></div>
        <form onSubmit={create} className="inline-form"><input placeholder="New album title" value={title} onChange={e => setTitle(e.target.value)} /><button className="primary">Create</button></form>
        {error && <div className="error">{error}</div>}
      </div>
      <div className="album-grid">
        {albums.map(album => <article className="album-card" key={album.id}><div className="album-mark">✦</div><h3>{album.title}</h3><p>{album.description || "A place for the moments that belong together."}</p><span className="tag">{album.role || album.privacy}</span></article>)}
        {albums.length === 0 && <div className="empty">No albums yet.</div>}
      </div>
    </section>
  );
}

function Chat({ user, rooms, selectedRoom, setSelectedRoom, onRefresh }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [targetUser, setTargetUser] = useState("");
  const [targetResults, setTargetResults] = useState([]);

  async function openRoom(room) {
    setSelectedRoom(room); setError("");
    try { const data = await api(`/api/chat/rooms/${room.id}/messages`); setMessages(data.messages || []); }
    catch (err) { setError(err.message); }
  }

  async function send(event) {
    event.preventDefault(); if (!selectedRoom || !text.trim()) return;
    try {
      const data = await api(`/api/chat/rooms/${selectedRoom.id}/messages`, { method: "POST", body: JSON.stringify({ content: text }) });
      setMessages(current => [...current, data.chat_message]); setText(""); await onRefresh();
    } catch (err) { setError(err.message); }
  }

  async function searchUsers(event) {
    const value = event.target.value; setTargetUser(value);
    if (value.trim().length < 2) { setTargetResults([]); return; }
    try { const data = await api(`/api/auth/users?q=${encodeURIComponent(value)}`); setTargetResults(data.users || []); }
    catch (_) { setTargetResults([]); }
  }

  async function startDirect(userId) {
    try {
      const data = await api("/api/chat/rooms", { method: "POST", body: JSON.stringify({ room_type: "direct", user_id: userId }) });
      setTargetUser(""); setTargetResults([]); await onRefresh(); openRoom(data.room);
    } catch (err) { setError(err.message); }
  }

  const roomLabel = useMemo(() => {
    if (!selectedRoom) return "Choose a conversation";
    if (selectedRoom.name) return selectedRoom.name;
    if (selectedRoom.room_type === "direct") return selectedRoom.members.filter(m => m.user_id !== user.id).map(m => m.display_name).join(", ") || "Direct chat";
    return `${selectedRoom.room_type} chat`;
  }, [selectedRoom]);

  return (
    <section className="chat-layout">
      <aside className="panel chat-sidebar">
        <div className="section-heading"><span>Conversations</span><small>{rooms.length}</small></div>
        <input placeholder="Find a person…" value={targetUser} onChange={searchUsers} />
        {targetResults.map(person => <button className="person-result" key={person.id} onClick={() => startDirect(person.id)}><strong>{person.display_name}</strong><small>@{person.username}</small></button>)}
        <div className="room-list">{rooms.map(room => <button key={room.id} className={selectedRoom?.id === room.id ? "room active" : "room"} onClick={() => openRoom(room)}><strong>{room.name || `${room.room_type} chat`}</strong><small>{room.member_count} people</small></button>)}</div>
      </aside>
      <div className="panel chat-window">
        <div className="chat-header"><strong>{roomLabel}</strong>{selectedRoom && <small>{selectedRoom.member_count} members</small>}</div>
        <div className="messages">
          {!selectedRoom && <div className="empty">Choose a chat, or search for someone to start one.</div>}
          {selectedRoom && messages.map(message => <div className={message.sender_id === user.id ? "bubble mine" : "bubble"} key={message.id}><small>{message.sender.display_name}</small><div>{message.content}</div><time>{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time></div>)}
        </div>
        {selectedRoom && <form className="message-form" onSubmit={send}><input placeholder="Write something…" value={text} onChange={e => setText(e.target.value)} /><button className="primary">Send</button></form>}
        {error && <div className="error">{error}</div>}
      </div>
    </section>
  );
}

export default function App() {
  const [auth, setAuthState] = useState(getStoredAuth());
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function load() {
      if (!auth.token) { setChecking(false); return; }
      try {
        const data = await api("/api/auth/me");
        setUser(data);
      } catch (_) {
        clearAuth(); setAuthState({ token: null, session: null });
      } finally { setChecking(false); }
    }
    load();
  }, []);

  if (checking) return <div className="loading">Opening Lunrea…</div>;
  if (!auth.token || !user) return <Auth onLogin={(token, nextUser) => { setAuth(token); setAuthState({ token, session: null }); setUser(nextUser); }} />;
  if (!auth.session) return <Unlock onUnlock={() => setAuthState(getStoredAuth())} onLogout={() => { clearAuth(); setAuthState({ token: null, session: null }); setUser(null); }} />;
  return <Dashboard user={user} onLogout={() => { clearAuth(); setAuthState({ token: null, session: null }); setUser(null); }} />;
}
