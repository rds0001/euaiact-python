"""Exact nonnegative rational arithmetic for qualified components."""

from fractions import Fraction


def _rational(regel, eingaben):
    if regel["operation"] == "MONATSBRUCH_30_TAGE":
        n, d = int(eingaben["monatsbruch_zaehler"]), int(eingaben["monatsbruch_nenner"])
        if n >= d:
            raise ValueError(
                "Monatsbruch muss kleiner als eins sein; ganze Monate kalendarisch behandeln"
            )
        wert = Fraction(30 * n, d)
        return {"zaehler": str(wert.numerator), "nenner": str(wert.denominator)}
    a = Fraction(
        int(eingaben[regel["zaehler_links"]]), int(eingaben[regel["nenner_links"]])
    )
    b = Fraction(
        int(eingaben[regel["zaehler_rechts"]]), int(eingaben[regel["nenner_rechts"]])
    )
    if regel.get("anteile_beide") and (a > 1 or b > 1):
        raise ValueError("JAE-Anteile duerfen eins nicht ueberschreiten")
    if regel.get("anteil_rechts") and b > 1:
        raise ValueError("Hinzurechnungsquote darf eins nicht ueberschreiten")
    wert = a + b if regel["operation"] == "RATIONALE_ADDITION" else a * b
    return {"zaehler": str(wert.numerator), "nenner": str(wert.denominator)}
