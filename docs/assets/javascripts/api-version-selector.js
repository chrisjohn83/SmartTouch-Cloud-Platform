const smartTouchApiVersions = [
  {
    section: "api-reference",
    api: "Device API",
    routes: { v1: "device-api", v2: "device-api-v2" }
  },
  {
    section: "api-reference",
    api: "Deployment API",
    routes: { v1: "deployment-api", v2: "deployment-api-v2" }
  },
  {
    section: "api-reference",
    api: "Audit Log API",
    routes: { v1: "audit-log-api", v2: "audit-log-api-v2" }
  },
  {
    section: "playground",
    api: "Device API Playground",
    routes: { v1: "device-api", v2: "device-api-v2" }
  },
  {
    section: "playground",
    api: "Deployment API Playground",
    routes: { v1: "deployment-api", v2: "deployment-api-v2" }
  },
  {
    section: "playground",
    api: "Audit Log API Playground",
    routes: { v1: "audit-log-api", v2: "audit-log-api-v2" }
  }
];

function currentApiVersionRoute() {
  const segments = window.location.pathname.split("/").filter(Boolean);
  const slug = (segments.at(-1) || "").replace(/\.html$/, "");
  const section = segments.at(-2) || "";

  for (const entry of smartTouchApiVersions) {
    if (entry.section !== section) {
      continue;
    }

    for (const [version, routeSlug] of Object.entries(entry.routes)) {
      if (routeSlug === slug) {
        return { entry, version, slug };
      }
    }
  }

  return null;
}

function versionTargetUrl(currentSlug, targetSlug) {
  const url = new URL(window.location.href);
  const htmlPath = `/${currentSlug}.html`;
  const directoryPath = `/${currentSlug}/`;

  if (url.pathname.endsWith(htmlPath)) {
    url.pathname = `${url.pathname.slice(0, -htmlPath.length)}/${targetSlug}.html`;
  } else if (url.pathname.endsWith(directoryPath)) {
    url.pathname = `${url.pathname.slice(0, -directoryPath.length)}/${targetSlug}/`;
  } else {
    url.pathname = url.pathname.replace(currentSlug, targetSlug);
  }

  return url.toString();
}

function initializeApiVersionSelector() {
  const route = currentApiVersionRoute();
  const content = document.querySelector(".md-content__inner");
  const heading = content?.querySelector("h1");

  if (!route || !content || !heading || content.querySelector(".st-api-version-selector")) {
    return;
  }

  const selectorId = `st-api-version-${route.entry.section}-${route.entry.routes.v1}`;
  const wrapper = document.createElement("div");
  wrapper.className = "st-api-version-selector";
  wrapper.setAttribute("role", "group");
  wrapper.setAttribute("aria-label", `${route.entry.api} version`);

  const label = document.createElement("label");
  label.htmlFor = selectorId;
  label.textContent = "API version";

  const select = document.createElement("select");
  select.id = selectorId;
  select.setAttribute("data-testid", "api-version-selector");

  const versions = [
    { value: "v1", label: "V1 — Stable" },
    { value: "v2", label: "V2 — Latest" }
  ];

  versions.forEach(({ value, label: optionLabel }) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = optionLabel;
    option.selected = value === route.version;
    select.appendChild(option);
  });

  select.addEventListener("change", () => {
    const targetSlug = route.entry.routes[select.value];
    if (targetSlug && targetSlug !== route.slug) {
      window.location.assign(versionTargetUrl(route.slug, targetSlug));
    }
  });

  const context = document.createElement("span");
  context.className = "st-api-version-context";
  context.textContent = route.entry.api;

  wrapper.append(label, select, context);
  heading.insertAdjacentElement("afterend", wrapper);
}

if (typeof document$ !== "undefined") {
  document$.subscribe(initializeApiVersionSelector);
} else if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeApiVersionSelector);
} else {
  initializeApiVersionSelector();
}
