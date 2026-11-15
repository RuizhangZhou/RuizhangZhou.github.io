(() => {
  const root = document.documentElement;
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const german = root.lang.startsWith("de");
  const blogTitle = document.querySelector("[data-blog-title]");
  if (blogTitle && new URLSearchParams(location.search).has("id")) {
    blogTitle.hidden = true;
  }
  const themeButton = document.querySelector("[data-theme-toggle]");
  const menuButton = document.querySelector("[data-menu-toggle]");
  const navigation = document.querySelector("#site-navigation");

  function setTheme(theme) {
    root.dataset.theme = theme;
    themeButton?.setAttribute("aria-pressed", String(theme === "dark"));
    themeButton?.setAttribute(
      "aria-label",
      german
        ? theme === "dark"
          ? "Helles Design einschalten"
          : "Dunkles Design einschalten"
        : theme === "dark"
          ? "Use light theme"
          : "Use dark theme",
    );
  }
  try {
    setTheme(localStorage.getItem("rick-theme") === "dark" ? "dark" : "light");
  } catch {
    setTheme("light");
  }
  themeButton?.addEventListener("click", () => {
    const theme = root.dataset.theme === "dark" ? "light" : "dark";
    setTheme(theme);
    try {
      localStorage.setItem("rick-theme", theme);
    } catch {
      /* Browsing can continue without storage. */
    }
  });

  function closeMenu() {
    menuButton?.setAttribute("aria-expanded", "false");
    navigation?.classList.remove("is-open");
  }
  menuButton?.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") !== "true";
    menuButton.setAttribute("aria-expanded", String(open));
    navigation?.classList.toggle("is-open", open);
  });
  navigation?.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.key !== "Escape" ||
      menuButton?.getAttribute("aria-expanded") !== "true"
    )
      return;
    closeMenu();
    menuButton.focus();
  });

  if ("IntersectionObserver" in window && !reducedMotion) {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.08 },
    );
    document.querySelectorAll("[data-reveal]").forEach((element) => {
      element.classList.add("reveal-ready");
      observer.observe(element);
    });
  }

  const progress = document.querySelector(".reading-progress");
  let scrollScheduled = false;
  function updateScroll() {
    const distance = document.documentElement.scrollHeight - innerHeight;
    if (progress)
      progress.style.transform = `scaleX(${distance > 0 ? scrollY / distance : 0})`;
    document
      .querySelector(".site-header")
      ?.classList.toggle("is-scrolled", scrollY > 16);
    scrollScheduled = false;
  }
  addEventListener(
    "scroll",
    () => {
      if (scrollScheduled) return;
      scrollScheduled = true;
      requestAnimationFrame(updateScroll);
    },
    { passive: true },
  );
  updateScroll();

  const dialog = document.querySelector("#project-dialog");
  const dialogBody = dialog?.querySelector("[data-dialog-body]");
  if (dialog && dialogBody && typeof dialog.showModal === "function") {
    document.querySelectorAll("[data-case]").forEach((button) => {
      button.hidden = false;
      button.addEventListener("click", () => {
        const template = document.getElementById(button.dataset.case);
        if (!(template instanceof HTMLTemplateElement)) return;
        dialogBody.replaceChildren(template.content.cloneNode(true));
        dialog.showModal();
      });
    });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  }

  const demoButton = document.querySelector("[data-routing-demo]");
  const demoStatus = document.querySelector("[data-routing-status]");
  const primary = document.querySelector('[data-route="primary"]');
  const fallback = document.querySelector('[data-route="fallback"]');
  const modeButtons = document.querySelectorAll("[data-routing-mode]");
  let mode = "before";
  let running = false;
  modeButtons.forEach((button) =>
    button.addEventListener("click", () => {
      if (running) return;
      mode = button.dataset.routingMode;
      modeButtons.forEach((item) =>
        item.setAttribute("aria-pressed", String(item === button)),
      );
      primary?.classList.remove("route-error");
      fallback?.classList.remove("route-active");
      if (demoStatus)
        demoStatus.textContent = german
          ? "Bereit für ein Beispiel."
          : "Ready for an example.";
    }),
  );
  demoButton?.addEventListener("click", async () => {
    if (running || !demoStatus) return;
    running = true;
    demoButton.disabled = true;
    modeButtons.forEach((button) => {
      button.disabled = true;
    });
    primary?.classList.remove("route-error");
    fallback?.classList.remove("route-active");
    demoStatus.textContent = german
      ? "Simulierte Anfrage wird verarbeitet …"
      : "Processing a simulated request…";
    await new Promise((resolve) =>
      setTimeout(resolve, reducedMotion ? 0 : 650),
    );
    primary?.classList.add("route-error");
    if (mode === "before") {
      demoStatus.textContent = german
        ? "Anbieter nicht verfügbar. Noch kein Text ausgegeben."
        : "Provider unavailable. No text has been shown yet.";
      await new Promise((resolve) =>
        setTimeout(resolve, reducedMotion ? 0 : 650),
      );
      fallback?.classList.add("route-active");
      demoStatus.textContent = german
        ? "Nächster Anbieter übernimmt. Eine zusammenhängende Antwort."
        : "The next provider takes over. One coherent answer.";
    } else {
      demoStatus.textContent = german
        ? "Ausgabe bereits begonnen. Unterbrechung anzeigen und einen neuen Versuch anbieten."
        : "Output already started. Surface the interruption and offer an explicit retry.";
    }
    running = false;
    demoButton.disabled = false;
    modeButtons.forEach((button) => {
      button.disabled = false;
    });
  });
})();
