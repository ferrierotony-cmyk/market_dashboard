# Portfolio builder

Generates the pages in site_extra/portfolio. Edit the text in build_site3.py, never in the generated html.

Rebuild from the repo root:

    mkdir /tmp/pf && cp -r site_extra/portfolio/assets /tmp/pf/
    python3 tools/portfolio_builder/build_site3.py /tmp/pf
    cp /tmp/pf/*.html /tmp/pf/style.css site_extra/portfolio/

Check that git diff shows only the pages you meant to change, then push to public-live. A push deploys GitHub Pages and Vercel.

mk_tender_banner.py redraws the Tender Tracker banner and thumbnail from the tender run's events.csv.
