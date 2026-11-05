# velocity-radar

Lists Velocity's event and program pages with their dates and signup links, read live from the public sitemap at velocityincubator.com. Use it to refresh the README's events table, or to see what's coming up. It needs Python 3.9+ and nothing else.

```bash
python radar.py                 # events in the next 60 days
python radar.py --days 120      # look further ahead
python radar.py --all           # every page, newest first, including past events and undated programs
python radar.py --markdown      # a Markdown table for the README
```

```
2026-11-16  The Co-op Workplace Simulation by Velocity    https://airtable.com/appsLpsmcadbUEjvA/pagazyQHGqQcAlgml/form
```

How it works: it reads `/sitemap.xml`, fetches each `/programs-events/` page politely (6 at a time, with a descriptive User-Agent), and pulls out the title, full dates such as "November 16, 2026", signup links (Fillout, Luma, Airtable, Ticketfi, Eventbrite, Microsoft Forms) and whether registration says closed.

Limits:
- Dates without a year, like "Nov 16", are ignored, because every page's sidebar repeats the next event in that form. A multi-week event shows only under its first full date.
- Page layout can change. If results look wrong, check the page itself. **The website is the source of truth.**

Tests (offline): `python -m unittest discover -s tests`
