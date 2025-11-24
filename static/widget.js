/**
 * Simple embeddable widget script.
 * Usage on your site (e.g. https://vaidrix.com/site):
 *
 * <script src="https://YOUR-SERVER-DOMAIN/widget.js" async></script>
 *
 * Make sure CORS is enabled on the Flask app.
 */

(function () {
  const API_URL = (window.VAIDRIX_MEETING_BOT_API || "https://your-domain.com/api/chat");

  function createWidget() {
    const container = document.createElement("div");
    container.style.position = "fixed";
    container.style.bottom = "20px";
    container.style.right = "20px";
    container.style.zIndex = "999999";

    container.innerHTML = `
      <style>
        .vdx-launcher-btn {
          width: 52px;
          height: 52px;
          border-radius: 999px;
          border: none;
          cursor: pointer;
          background: radial-gradient(circle at top left, #22d3ee, #6366f1);
          box-shadow: 0 12px 30px rgba(0,0,0,0.45);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #020617;
          font-weight: 700;
          font-size: 20px;
        }
        .vdx-chat-window {
          position: fixed;
          bottom: 88px;
          right: 20px;
          width: 340px;
          max-height: 480px;
          background: #020617;
          border-radius: 18px;
          border: 1px solid rgba(148, 163, 184, 0.5);
          box-shadow: 0 24px 60px rgba(0,0,0,0.65);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .vdx-chat-header {
          padding: 10px 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          background: radial-gradient(circle at top left, #1d4ed8, #020617);
          border-bottom: 1px solid rgba(51, 65, 85, 0.9);
          color: #e5e7eb;
        }
        .vdx-chat-avatar {
          width: 30px;
          height: 30px;
          border-radius: 999px;
          background: linear-gradient(135deg, #22d3ee, #6366f1);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          font-weight: 700;
          color: #020617;
        }
        .vdx-chat-title {
          font-size: 13px;
          font-weight: 600;
        }
        .vdx-chat-subtitle {
          font-size: 11px;
          color: #cbd5f5;
        }
        .vdx-chat-body {
          padding: 8px;
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 6px;
          overflow-y: auto;
          background: #020617;
        }
        .vdx-msg {
          max-width: 80%;
          padding: 6px 8px;
          border-radius: 11px;
          font-size: 12px;
          line-height: 1.35;
          word-break: break-word;
        }
        .vdx-msg-bot {
          align-self: flex-start;
          background: #111827;
          border: 1px solid rgba(55, 65, 81, 0.9);
          color: #e5e7eb;
        }
        .vdx-msg-user {
          align-self: flex-end;
          background: #2563eb;
          color: white;
          border-bottom-right-radius: 4px;
        }
        .vdx-chat-footer {
          border-top: 1px solid rgba(31, 41, 55, 0.95);
          padding: 6px;
          display: flex;
          gap: 4px;
          background: #020617;
        }
        .vdx-chat-input {
          flex: 1;
          border-radius: 999px;
          border: 1px solid rgba(51, 65, 85, 0.9);
          padding: 6px 10px;
          font-size: 12px;
          background: #020617;
          color: #e5e7eb;
          outline: none;
        }
        .vdx-chat-input::placeholder {
          color: #6b7280;
        }
        .vdx-chat-send {
          border-radius: 999px;
          border: none;
          padding: 6px 12px;
          font-size: 12px;
          font-weight: 500;
          background: linear-gradient(135deg, #22d3ee, #6366f1);
          color: #020617;
          cursor: pointer;
        }
        .vdx-chat-send:disabled {
          opacity: 0.5;
          cursor: default;
        }
      </style>
      <button class="vdx-launcher-btn" aria-label="Open meeting assistant">V</button>
    `;

    document.body.appendChild(container);

    const launcherBtn = container.querySelector(".vdx-launcher-btn");
    let chatWindow = null;

    function appendMessage(bodyEl, text, who) {
      const div = document.createElement("div");
      div.className = "vdx-msg " + (who === "bot" ? "vdx-msg-bot" : "vdx-msg-user");
      div.innerText = text;
      bodyEl.appendChild(div);
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }

    function createChatWindow() {
      if (chatWindow) return;
      chatWindow = document.createElement("div");
      chatWindow.className = "vdx-chat-window";
      chatWindow.innerHTML = `
        <div class="vdx-chat-header">
          <div class="vdx-chat-avatar">V</div>
          <div>
            <div class="vdx-chat-title">Vaidrix Meeting Assistant</div>
            <div class="vdx-chat-subtitle">Book a call in seconds</div>
          </div>
        </div>
        <div class="vdx-chat-body"></div>
        <form class="vdx-chat-footer">
          <input class="vdx-chat-input" placeholder="Ask me to book a call..." />
          <button class="vdx-chat-send" type="submit">Send</button>
        </form>
      `;
      document.body.appendChild(chatWindow);

      const bodyEl = chatWindow.querySelector(".vdx-chat-body");
      const formEl = chatWindow.querySelector(".vdx-chat-footer");
      const inputEl = chatWindow.querySelector(".vdx-chat-input");
      const sendEl = chatWindow.querySelector(".vdx-chat-send");

      appendMessage(bodyEl,
        "Hi! I can help you schedule a meeting with the Vaidrix team. " +
        "Tell me your preferred date/time and your email.",
        "bot"
      );

      formEl.addEventListener("submit", async function (e) {
        e.preventDefault();
        const text = inputEl.value.trim();
        if (!text) return;
        appendMessage(bodyEl, text, "user");
        inputEl.value = "";
        inputEl.focus();
        sendEl.disabled = true;

        try {
          const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
          });
          const data = await res.json();
          appendMessage(bodyEl, data.reply || "No reply.", "bot");
        } catch (err) {
          console.error(err);
          appendMessage(bodyEl, "Error talking to server. Please try again.", "bot");
        } finally {
          sendEl.disabled = false;
        }
      });
    }

    launcherBtn.addEventListener("click", function () {
      if (!chatWindow) {
        createChatWindow();
      } else {
        const isHidden = chatWindow.style.display === "none";
        chatWindow.style.display = isHidden ? "flex" : "none";
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createWidget);
  } else {
    createWidget();
  }
})();
