# Changelog

All notable changes to the Iluminação LED Niterói project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-07-08

### Added

- **Theme Toggle (Dark/Light Mode)** — New button in navbar to switch between dark and light themes
  - User preference saved to localStorage
  - Syncs with system preference (prefers-color-scheme media query)
  - Smooth CSS transitions between themes

- **Zoom Minimum Validation** — New constraint for point creation
  - Points can only be created when zoom level ≥18
  - Cursor changes to pointer when hovering over map at valid zoom
  - Prevents accidental point creation at low zoom levels

- **Nominatim Address Auto-fill** — Automatic address lookup on point creation/editing
  - Reverse geocoding using OpenStreetMap Nominatim API
  - Address field automatically populated when selecting location
  - Non-blocking background request (doesn't freeze UI)

- **Security Improvements**
  - Environment variable support for Supabase credentials
  - Hardcoded credentials replaced with `window.__CONFIG__` pattern
  - `.env.example` template with secure placeholders

- **Documentation** — NEW files
  - CHANGELOG.md — This file
  - .editorconfig — Code style consistency
  - Updated README, DEPLOYMENT_GUIDE, IMPROVEMENTS_SUMMARY

### Removed

- **Approval Workflow System** — Simplified editor workflow
  - Removed approval UI from admin panel
  - Editors can now update points directly
  - Admins retain full access

- **Obsolete Documentation** — Phase-specific docs consolidated

### Fixed

- **Theme Button Positioning** — Fixed navbar layout issues
- **GitHub Actions Versions** — Upgraded to v4 (checkout, setup-node)
- **Snyk Action** — Pinned to v0.4.0 (security best practice)

### Changed

- **Editor Permissions** — Direct edit access without approval queue
- **GitHub Actions** — Added npm caching for faster builds

---

## [1.1.0] - 2026-07-01

### Added

- Dark/Light theme toggle with system preference sync
- Plausible Analytics integration
- Rate limiting for RPC requests
- End-to-End tests via Playwright
- Lighthouse CI for performance monitoring
- Security scanning (npm audit + OWASP ZAP)
- Load testing via k6
- API testing via Postman/Newman

---

## [1.0.0] - 2026-06-15

### Added

- Initial Release - Core GIS Application
  - Interactive map with Leaflet.js
  - Point creation/editing
  - Role-based access control
  - CSV/GeoJSON/PDF export
  - Supabase integration
  - Netlify deployment

---

**Last Updated:** 2026-07-08
