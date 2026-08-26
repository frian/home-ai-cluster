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
    const margin = 16;

    if (activeRect.top < tocRect.top + margin) {
      toc.scrollTop -= tocRect.top + margin - activeRect.top;
    } else if (activeRect.bottom > tocRect.bottom - margin) {
      toc.scrollTop += activeRect.bottom - (tocRect.bottom - margin);
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
