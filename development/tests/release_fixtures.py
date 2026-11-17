"""Generated EPTS cases; no match data or labels are read."""
from pathlib import Path
from test_ball_gap_candidate import positive_fixture
from test_input_contract import fixture


def release_fixture(root: Path, case: str = 'positive'):
    root.mkdir(parents=True, exist_ok=True)
    meta, raw, quality = positive_fixture(root)
    if case == 'invalid':
        lines = quality.read_text().splitlines()
        for i in range(220, 280):
            fields = lines[i + 1].split(',')
            fields[1] = '0'
            lines[i + 1] = ','.join(fields)
        quality.write_text('\n'.join(lines) + '\n')
    elif case == 'unsupported':
        raw.write_text(''.join(line.rsplit(':', 1)[0] + ':nan,nan,nan\n'
                               for line in raw.read_text().splitlines()))
    elif case != 'positive':
        raise ValueError('Unknown synthetic release case')
    return meta, raw, quality


def tactical_fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    return fixture(root, 199319)
