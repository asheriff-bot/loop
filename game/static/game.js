(() => {
  const CODE_LENGTH = 4;
  const state = {
    gameId: null,
    current: [],
    finished: false,
  };

  const els = {
    lobby: document.getElementById("lobby"),
    board: document.getElementById("board"),
    playerName: document.getElementById("playerName"),
    startBtn: document.getElementById("startBtn"),
    digitPad: document.getElementById("digitPad"),
    currentGuess: document.getElementById("currentGuess"),
    history: document.getElementById("history"),
    statusText: document.getElementById("statusText"),
    remainingText: document.getElementById("remainingText"),
    resultBanner: document.getElementById("resultBanner"),
    submitBtn: document.getElementById("submitBtn"),
    backspaceBtn: document.getElementById("backspaceBtn"),
    newGameBtn: document.getElementById("newGameBtn"),
    scoreList: document.getElementById("scoreList"),
    refreshScores: document.getElementById("refreshScores"),
  };

  function selectedMode() {
    const el = document.querySelector('input[name="mode"]:checked');
    return el ? el.value : "classic";
  }

  function renderSlots() {
    els.currentGuess.innerHTML = "";
    for (let i = 0; i < CODE_LENGTH; i++) {
      const slot = document.createElement("div");
      slot.className = "slot" + (state.current[i] != null ? " filled" : "");
      slot.textContent = state.current[i] != null ? state.current[i] : "·";
      els.currentGuess.appendChild(slot);
    }
  }

  function buildPad() {
    els.digitPad.innerHTML = "";
    for (let d = 1; d <= 6; d++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = String(d);
      btn.addEventListener("click", () => {
        if (state.finished || state.current.length >= CODE_LENGTH) return;
        state.current.push(d);
        renderSlots();
      });
      els.digitPad.appendChild(btn);
    }
  }

  async function api(path, options) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options && options.headers) },
      ...options,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `Request failed (${res.status})`);
    }
    return data;
  }

  function renderHistory(guesses) {
    els.history.innerHTML = "";
    for (const g of guesses || []) {
      const li = document.createElement("li");
      li.innerHTML = `
        <span>${g.guess.join(" ")}</span>
        <span class="pegs">
          <span class="peg exact">${g.exact} exact</span>
          <span class="peg partial">${g.partial} partial</span>
        </span>`;
      els.history.appendChild(li);
    }
  }

  async function refreshScores() {
    const mode = selectedMode();
    const data = await api(`/api/scores?mode=${encodeURIComponent(mode === "daily" ? "daily" : "classic")}`);
    els.scoreList.innerHTML = "";
    if (!data.scores.length) {
      els.scoreList.innerHTML = "<li>No wins yet — be the first.</li>";
      return;
    }
    for (const s of data.scores) {
      const li = document.createElement("li");
      const daily = s.challenge_date ? ` · daily ${s.challenge_date}` : "";
      li.innerHTML = `<strong>${s.score}</strong> — ${escapeHtml(s.player_name)}
        <span class="meta">${s.guesses_used} guesses · ${s.mode || "classic"}${daily}</span>`;
      els.scoreList.appendChild(li);
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  async function startGame() {
    const body = {
      player_name: els.playerName.value.trim() || "Player",
      mode: selectedMode(),
    };
    const data = await api("/api/games", { method: "POST", body: JSON.stringify(body) });
    state.gameId = data.game_id;
    state.current = [];
    state.finished = false;
    els.lobby.classList.add("hidden");
    els.board.classList.remove("hidden");
    els.resultBanner.classList.add("hidden");
    els.statusText.textContent =
      data.mode === "daily"
        ? `Daily challenge ${data.challenge_date}`
        : "Classic vault — make a guess";
    els.remainingText.textContent = `${data.max_guesses} guesses left`;
    renderSlots();
    renderHistory([]);
    await refreshScores();
  }

  async function submitGuess() {
    if (state.finished) return;
    if (state.current.length !== CODE_LENGTH) {
      els.statusText.textContent = "Enter 4 digits first";
      return;
    }
    try {
      const data = await api(`/api/games/${state.gameId}/guess`, {
        method: "POST",
        body: JSON.stringify({ guess: state.current }),
      });
      state.current = [];
      renderSlots();
      renderHistory(data.game.guesses);
      els.remainingText.textContent = `${data.remaining} guesses left`;

      if (data.status === "won") {
        state.finished = true;
        els.resultBanner.className = "banner won";
        els.resultBanner.textContent = `Unlocked! Score ${data.score}. Code was ${data.game.secret.join(" ")}`;
        els.resultBanner.classList.remove("hidden");
        els.statusText.textContent = "You cracked the lock";
        await refreshScores();
      } else if (data.status === "lost") {
        state.finished = true;
        els.resultBanner.className = "banner lost";
        els.resultBanner.textContent = `Lock sealed. Code was ${data.game.secret.join(" ")}`;
        els.resultBanner.classList.remove("hidden");
        els.statusText.textContent = "Out of guesses";
      } else {
        els.statusText.textContent = `${data.exact} exact · ${data.partial} partial`;
      }
    } catch (err) {
      els.statusText.textContent = err.message;
    }
  }

  els.startBtn.addEventListener("click", () => startGame().catch((e) => alert(e.message)));
  els.submitBtn.addEventListener("click", () => submitGuess());
  els.backspaceBtn.addEventListener("click", () => {
    state.current.pop();
    renderSlots();
  });
  els.newGameBtn.addEventListener("click", () => {
    els.board.classList.add("hidden");
    els.lobby.classList.remove("hidden");
  });
  els.refreshScores.addEventListener("click", () => refreshScores().catch(console.error));
  document.querySelectorAll('input[name="mode"]').forEach((el) => {
    el.addEventListener("change", () => refreshScores().catch(console.error));
  });

  buildPad();
  renderSlots();
  refreshScores().catch(console.error);
})();
