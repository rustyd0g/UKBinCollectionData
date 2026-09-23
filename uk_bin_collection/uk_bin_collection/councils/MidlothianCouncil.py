from datetime import datetime

import requests

from uk_bin_collection.uk_bin_collection.common import *
from uk_bin_collection.uk_bin_collection.get_bin_data import AbstractGetBinDataClass


class CouncilClass(AbstractGetBinDataClass):
    """
    Midlothian Council bin collection scraper.

    Data source: my.midlothian.gov.uk runs on Granicus govService. The
    public-facing form at /service/Bin_Collection_Dates posts to the
    platform's "apibroker" runLookup endpoint with a fixed lookup ID and
    a JSON body containing the user's UPRN. The API returns a JSON
    response whose `integration.transformed.rows_data` field is a dict
    of collection rows.

    Maintainer notes:
    -----------------
    * LOOKUP_ID below is the govService form/integration ID. If the council
      ever rebuilds or republishes the form, this ID will change and the
      scraper will start returning 200 with an error response (not a 4xx).
      To find the new ID, open the bin collection page in a browser, watch
      the network tab for a POST to `/apibroker/runLookup`, and copy the
      `id` query parameter.
    * The form was originally built around an address-list dropdown
      (`listAddress`) and a hidden UPRN field. We submit the UPRN for both
      because the backend resolves them identically, which avoids needing
      a second call to fetch the address list.
    * The `Date` field comes back as "DD/MM/YYYY HH:MM:SS" — already in the
      format the project expects, so we just strip the time component.
    * Some properties don't receive every collection type (e.g. no garden
      bin). The API simply omits those rows, so no special handling is
      needed beyond the per-row null check.
    """

    LOOKUP_ID = "69a19ba76d3a2"
    BASE_URL = "https://my.midlothian.gov.uk"
    LANDING_PAGE = f"{BASE_URL}/service/Bin_Collection_Dates"
    API_URL = f"{BASE_URL}/apibroker/runLookup"
    REQUEST_TIMEOUT = 120

    # The API returns internal service names ("Residual Collection Service",
    # "Card Collection Service", etc.) but the council's public-facing
    # materials refer to bins by colour. We map to the user-facing names so
    # the output matches what residents see on bin stickers and the council
    # website. Unmapped values fall through unchanged so a new bin type
    # added by the council still produces output (under its raw API name)
    # rather than disappearing.
    SERVICE_NAME_MAP = {
        "Glass Collection Service": "Glass Box",
        "Card Collection Service": "Green Bin",
        "Food Collection Service": "Food Bin",
        "Garden Collection Service": "Brown Bin",
        "Residual Collection Service": "Grey Bin",
        "Recycling Collection Service": "Blue Bin",
    }

    def parse_data(self, page: str, **kwargs) -> dict:
        uprn = kwargs.get("uprn")
        if not uprn:
            raise ValueError("Midlothian Council requires a UPRN (--uprn)")
        uprn = str(uprn).strip()
        check_uprn(uprn)
        if not uprn.isdigit() or len(uprn) > 12:
            raise ValueError(
                "Midlothian Council requires a numeric UPRN of up to 12 digits"
            )

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # Prime the session — the apibroker endpoint requires a PHPSESSID
        # cookie that's only set when the landing page is fetched first.
        # requests.Session() handles cookie persistence automatically.
        session.get(self.LANDING_PAGE, timeout=self.REQUEST_TIMEOUT).raise_for_status()

        response = session.post(
            self.API_URL,
            params={
                "id": self.LOOKUP_ID,
                "noRetry": "false",
                "app_name": "AF-Renderer::Self",
            },
            json={
                "formValues": {
                    "Section 1": {
                        "uprn": {"value": uprn},
                        "listAddress": {"value": uprn},
                        "fromDate": {"value": datetime.now().strftime("%Y-%m-%d")},
                    }
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*",
                "Referer": f"{self.BASE_URL}/fillform/?iframe_id=fillform-frame-1",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=self.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        payload = response.json()

        # The API returns 200 even on logical errors (bad UPRN, expired
        # session, etc.) — the `status` field is the real success signal.
        status = payload.get("status")
        if status != "done":
            raise ValueError(
                f"govService apibroker returned unexpected status '{status}'. "
                f"Full payload: {payload!r}"
            )

        rows = (
            payload.get("integration", {}).get("transformed", {}).get("rows_data") or {}
        )

        data = {"bins": []}
        for row in rows.values():
            service = row.get("Service")
            date_raw = (row.get("Date") or "").strip()
            if not (service and date_raw):
                continue
            try:
                collection_date = datetime.strptime(
                    date_raw.split()[0], "%d/%m/%Y"
                )
            except (IndexError, ValueError):
                continue
            data["bins"].append(
                {
                    "type": self.SERVICE_NAME_MAP.get(service, service),
                    "collectionDate": collection_date.strftime("%d/%m/%Y"),
                }
            )

        if not data["bins"]:
            raise ValueError(
                "No bin collections returned for UPRN. The UPRN may be "
                "invalid for Midlothian Council, or the API response shape "
                "may have changed."
            )

        # Defensive sort — the API currently returns rows in date order,
        # but that's not documented behaviour, so don't rely on it.
        data["bins"].sort(
            key=lambda b: datetime.strptime(b["collectionDate"], "%d/%m/%Y")
        )

        return data
