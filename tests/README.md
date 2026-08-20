# Tests

Ohne Einrichtung ausfuehrbar, keine externen Dienste:

```
.venv/bin/python tests/test_conditions.py    # Bedingungsparser
.venv/bin/python tests/test_befund.py        # Regelwerk gegen die Fixture
```

`tests/test_befund.py` prueft die handgeschriebene Fixture
`data/fixtures/viagogo/` gegen das echte Regelwerk. Verschiebt sich ein
Befund, bricht der Test — dann bitte hinsehen und den erwarteten Wert
bewusst aendern, nicht stillschweigend anpassen.
