"""Additional external data identities; no training split or model changes."""

ADDITIONAL_SKILLCORNER = (
    '1899585', '1925299', '1927964', '1953632', '1959846',
    '1986691', '1996435', '1996436', '2006229', '2006363',
)
ADDITIONAL_CASES = tuple('skillcorner-' + m for m in ADDITIONAL_SKILLCORNER)
