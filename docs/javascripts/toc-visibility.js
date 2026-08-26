(() => {
  const toc = document.getElementById("toc");
  if (!toc) {
    return;
  }

  const keepActiveLinkVisible = () => {
    const active = toc.querySelector('a[data-active="true"]');
    if (!active) {
      return;
    }

    const tocRect = toc.getBoundingClientRect();
    const activeRect = active.getBoundingClientRect();
    const header = toc.querySelector(":scope > div > p");
    const headerHeight = header?.getBoundingClientRect().height ?? 0;
    const topMargin = headerHeight + 16;
    const bottomMargin = 16;

    if (activeRect.top < tocRect.top + topMargin) {
      toc.scrollTop -= tocRect.top + topMargin - activeRect.top;
    } else if (activeRect.bottom > tocRect.bottom - bottomMargin) {
      toc.scrollTop += activeRect.bottom - (tocRect.bottom - bottomMargin);
    }
  };

  const observer = new MutationObserver((mutations) => {
    if (
      mutations.some(
        (mutation) =>
          mutation.type === "attributes" &&
          mutation.attributeName === "data-active" &&
          mutation.target.dataset.active === "true",
      )
    ) {
      keepActiveLinkVisible();
    }
  });

  toc.querySelectorAll("a[data-active]").forEach((link) => {
    observer.observe(link, { attributes: true, attributeFilter: ["data-active"] });
  });

  keepActiveLinkVisible();
})();
