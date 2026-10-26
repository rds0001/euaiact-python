"""Explicit publication date and optional later revocation effect; no calendar shift."""

from datetime import timedelta
from .fristen import _datum


def _widerruf_wirksamkeit(data):
    publication = _datum(data["widerruf_amtsblattdatum"])
    try:
        effect = publication + timedelta(days=1)
    except OverflowError:
        raise ValueError("Wirksamkeit ausserhalb des ISO-Datumsbereichs") from None
    if data["widerruf_spaeterer_tag_festgelegt"]:
        later = _datum(data["widerruf_festgelegter_tag"])
        if later < effect:
            raise ValueError(
                "Festgelegter Wirksamkeitstag liegt vor dem Tag nach Veroeffentlichung"
            )
        effect = later
    return dict(
        wirksam_ab=effect.isoformat(),
        am_prueftag_wirksam=_datum(data["widerruf_prueftag"]) >= effect,
    )
