# Driver image update — 22 October 2026

Real public photographs were discovered through web search and Wikipedia article lead images, then checked against the individual Wikimedia Commons file descriptions for authorship and licence. Only reviewed, successfully downloaded files enter the UI catalog. Original source files are preserved locally; CSS handles the card framing and fades. Metadata and full source links are in `frontend/public/portraits/credits.json` and Methods → Driver photography.

15 images were installed. Wikimedia’s image server returned HTTP 429 with Retry-After: 600 for remaining files; the downloader stopped rather than repeatedly retrying. Initials remain available for those drivers and for any failed image load. Future retries are manual, not an ongoing background task.

No calendars, participant lists, team assignments, telemetry processing, or mathematics were altered for this visual update.

Browser verification: all 15 installed images loaded successfully; the 390 px mobile layout had equal document and scroll widths (390 px), with readable names and lap times. Desktop and mobile screenshots are saved as driver-photos-desktop.jpg and driver-photos-mobile.jpg. Production build and the existing 3 frontend tests passed.
