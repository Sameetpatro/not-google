# NotGoogle Frontend (React 19 + Vite + Tailwind CSS)

The client application for **NotGoogle**, delivering a pixel-accurate, authentic Google search engine experience augmented with Search Generative Experience (SGE) AI Overviews, interactive crawler controls, and light/dark theme toggle.

> 💡 For complete full-stack documentation and system architecture, check the [Root README](../README.md).

---

## ✨ Features

- **Google-Authentic Presentation**: Multi-colored "NotGoogle" logo mark, search input with clear/voice/lens triggers, and standard Google result layouts with domain favicons and breadcrumbs.
- **Search Generative Experience (SGE)**: Instant AI Overview card with cited source chips that users can click to inspect referenced web documents.
- **Live Crawler Dashboard Modal**: Interactive floating status badge that polls `/crawler/status` and opens a modal with real-time statistics (pages crawled, pages indexed, queue size, duplicates skipped) and a manual keyword/URL seeder.
- **Light & Dark Theme**: Full theme switching with automatic contrast adjustment across all search elements and modals.
- **SearXNG Knowledge Sidebar**: Side-by-side search results and Wikipedia infobox cards for popular entities.
- **NotGooooogle Pagination**: Classic numbered pagination bar allowing effortless navigation through search results.

---

## 🚀 Running the Frontend

```bash
# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The application will be live at `http://localhost:5173`.
