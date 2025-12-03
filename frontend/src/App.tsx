import { Link, Route, Routes } from "react-router-dom";
import { HomePage } from "./pages/Home";
import { ProductDetailPage } from "./pages/ProductDetail";
import { ChatPage } from "./pages/Chat";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <Link to="/" className="logo">
            Traya Assistant
          </Link>
          <nav className="nav">
            <Link to="/">Home</Link>
            <Link to="/chat">Chat</Link>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products/:id" element={<ProductDetailPage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}


