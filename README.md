# LitSift

<a href="https://github.com/ekjaisal/LitSift/releases"><img height=20 alt="GitHub Release" src="https://img.shields.io/github/v/release/ekjaisal/LitSift?color=66023C&label=Release&labelColor=141414&style=flat-square&logo=github&logoColor=F5F3EF&logoWidth=11"></a> <a href="https://github.com/ekjaisal/LitSift/releases"><img height=20 alt="GitHub Downloads" src="https://img.shields.io/github/downloads/ekjaisal/LitSift/total?color=66023C&label=Downloads&labelColor=141414&style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0Y1RjNFRiI+PHBhdGggZD0iTTEyIDIwbC03LTcgMS40MS0xLjQxTDExIDE2LjE3VjRoMnYxMi4xN2w0LjU5LTQuNThMMTkgMTNsLTcgN3oiLz48L3N2Zz4=&logoColor=F5F3EF"></a> <a href="https://github.com/ekjaisal/LitSift/blob/main/LICENSE"><img height=20 alt="License: MIT" src="https://img.shields.io/badge/License-MIT-66023C?style=flat-square&labelColor=141414&logoColor=F5F3EF&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0Y1RjNFRiI+PHBhdGggZD0iTTE0IDJINmMtMS4xIDAtMiAuOS0yIDJ2MTZjMCAxLjEuOSAyIDIgMmgxMmMxLjEgMCAyLS45IDItMlY4bC02LTZ6bTQgMThINlY0aDd2NWg1djExeiIvPjwvc3ZnPg=="></a> <a href="https://github.com/ekjaisal/LitSift/blob/main/CITATION.cff"><img height=20 alt="Citation File" src="https://img.shields.io/badge/Citation-CFF-66023C?style=flat-square&labelColor=141414&logoColor=F5F3EF&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0Y1RjNFRiI+PHBhdGggZD0iTTYgMTdoM2wyLTRWN0g1djZoM3ptOCAwaDNsMi00VjdoLTZ2NmgzeiIvPjwvc3ZnPg=="></a> <a href="https://www.codefactor.io/repository/github/ekjaisal/litsift/overview/main"><img height=20 alt="CodeFactor" src="https://img.shields.io/codefactor/grade/github/ekjaisal/litsift/main?style=flat-square&labelColor=141414&logo=codefactor&logoColor=F5F3EF&label=Code%20Quality&logoWidth=11"></a> <a href="https://securityscorecards.dev/viewer/?uri=github.com/ekjaisal/LitSift"><img height=20 alt="OpenSSF Scorecard" src="https://img.shields.io/ossf-scorecard/github.com/ekjaisal/LitSift?label=OpenSSF%20Scorecard&style=flat-square&labelColor=141414&logoColor=F5F3EF"></a> <a href="https://github.com/ekjaisal/LitSift/stargazers"><img height=20 alt="GitHub Stars" src="https://img.shields.io/github/stars/ekjaisal/LitSift?color=66023C&style=flat-square&labelColor=141414&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0Y1RjNFRiI+PHBhdGggZD0iTTEyIDJsMy4wOSA2LjI2TDIyIDkuMjdsLTUgNC44N2wxLjE4IDYuODhMMTIgMTcuNzdsLTYuMTggMy4yNUw3IDE0LjE0IDIgOS4yN2w2LjkxLTEuMDFMMTIgMnoiLz48L3N2Zz4=&logoColor=F5F3EF&label=Stars"></a> <a href="https://github.com/ekjaisal"><img height=20 alt="Maintained by Jaisal E. K." src="https://img.shields.io/badge/Maintained_by-Jaisal_E._K.-66023C?style=flat-square&labelColor=141414&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0Y5RjlGNCI+PHBhdGggZD0iTTEyIDEyYzIuMjEgMCA0LTEuNzkgNC00cy0xLjc5LTQtNC00LTQgMS43OS00IDQgMS43OSA0IDQgNHptMCAyYy0yLjY3IDAtOCAxLjM0LTggNHYyaDE2di0yYzAtMi42Ni01LjMzLTQtOC00eiIvPjwvc3ZnPg==&logoColor=F5F3EF"></a>

LitSift is an intuitive implementation for searching [Semantic Scholar](https://www.semanticscholar.org) and saving filtered results as BibTeX/CSV. It provides a seamless and easy-to-use Graphical User Interface (GUI) for researchers to fetch results, based on the query, from Semantic Scholar's extensive database of academic literature and quickly sift through them using Boolean operators, wildcards, field-specific search, etc., to identify sources relevant to their research.

![LitSift Main Interface](assets/screenshots/main_interface.jpg)

## Features 🌟

  -  🔎 Search Semantic Scholar's vast database of academic literature and fetch up to 1000 results per query.
  -  📋 Retrieve endpoints: `title`, `authors`, `year`, `citationCount`, `influentialCitationCount`, `tldr`, `abstract`, `venue`, `publicationTypes`, `externalIds`, `openAccessPdf`, `url`, `citationStyles`
  -  ☑️ Preview and filter results using Boolean operators, wildcard matching, phrase matching, `field:term` search, complex query nesting, etc.
  -  👀 View the available details for each result in a convenient and easy-to-read window.
  -  📄 Follow links to open access PDFs when available.
  -  💾 Save all previewed, filtered or selected results to BibTeX/CSV.
  -  😌 Fetch results efficiently without hassles or having to deal with code.
  -  💡 Minimal and intuitive user interface with dark and light modes.

![LitSift Main Interface](assets/screenshots/preview_light.jpg)

![LitSift Main Interface](assets/screenshots/preview_dark.jpg)

## Usage 💻

1.  Download the latest release from the [Releases](https://github.com/ekjaisal/LitSift/releases) page.
2.  Set up LitSift on the device using the installer.
3.  Point and click to launch.
4.  Enter the query in the search box.
5.  Set the maximum number of results to fetch (up to 1000).
6.  Click 'Search' or hit 'Enter' to initiate the search.
7.  View and filter the fetched results in the 'Preview and Sift Results' tab using simple or complex queries (see tips).
8.  Double-click on the result to view all the available details in a single window.
9.  Double-click on the 'PDF URL' column to follow links to open access PDFs when available.
10.  Select results and click 'Save Selected' or apply filters and click 'Save Preview' to export all the visible results to BibTeX/CSV.
11.  Click 'Reset' to start over and fetch results for a new query.

## Attribution 🙂

LitSift uses publicly accessible endpoints of the [Semantic Scholar Academic Graph API](https://www.semanticscholar.org/product/api) without authentication. All data is fetched directly from [Semantic Scholar](https://www.semanticscholar.org).

## License 📄

This project is licensed under the MIT License. Please see the [LICENSE](LICENSE) file for details.

## Disclaimer 📣

This tool is provided as-is, without any warranties. Users are responsible for ensuring that their use of this implementation and the Semantic Scholar API complies with [Semantic Scholar's terms of service](https://www.semanticscholar.org/product/api).

## Acknowledgements 🤝🏾

LitSift has benefitted significantly from some of the many ideas and suggestions of [Sarath Kurmana](https://github.com/sarathkurmana), the assistance of Anthropic's [Claude 3.5 Sonnet](https://www.anthropic.com/news/claude-3-5-sonnet) with all the heavy lifting, feedback from [Dhananjayan T. Ashok](https://in.linkedin.com/in/dhananjayan-ashok-geology) and [Jayakrishnan S. S.](https://www.linkedin.com/in/jayakrishnan-s-s-342416181), [Muhammed Rashid's](https://github.com/muhammedrashidx) encouragement, and [Vishnu Rajagopal's](https://vishnurajagopal.in) support.


<a href="https://www.buymeacoffee.com/ekjaisal" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 160px !important;" ></a>
