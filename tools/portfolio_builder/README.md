# Portfolio builder

Generates the pages in site_extra/portfolio. Edit the text in build_site3.py, never in the generated html.

Rebuild from the repo root:

    mkdir /tmp/pf && cp -r site_extra/portfolio/assets /tmp/pf/
    python3 tools/portfolio_builder/build_site3.py /tmp/pf
    cp /tmp/pf/*.html /tmp/pf/tokens.css /tmp/pf/style.css site_extra/portfolio/

Check that git diff shows only the pages you meant to change, then push to public-live. A push deploys GitHub Pages and Vercel.

## Styling

All styling lives in two files under styles/. The build copies them into the output.

- styles/tokens.css holds every colour, size, space, radius and type step, plus the light and dark theme roles. Change a value here and it changes everywhere.
- styles/site.css holds the components. It uses tokens only. It has no raw colours and no raw sizes apart from media query widths.

build_site3.py and the psky modules write no style attributes. A photo that needs a focal point gets a class from fp, and the build adds the matching rule to the end of style.css.

mk_tender_banner.py redraws the Tender Tracker banner and thumbnail from the tender run's events.csv.
