import copy
import pytest
from scripts.acquire_asm01_canonical_v2 import canonical_identities


EXCEPTION=dict(path='Dataset/W6/15.5.TXT',bytes=9459)


def fixture_records():
    return [dict(path=f'Dataset/W{w}/{c}.{w}.TXT',bytes=500) for w in range(1,46) for c in range(1,184)]+[copy.deepcopy(EXCEPTION)]


def test_canonical_membership_preserves_all8235_native_samples_and_records_foreign_member():
    records=fixture_records();members=canonical_identities(records,EXCEPTION)
    assert len(members)==8235 and members[5,15]=='Dataset/W5/15.5.TXT'
    assert members[6,15]=='Dataset/W6/15.6.TXT'
    assert len(records)==8236 and EXCEPTION in records


@pytest.mark.parametrize('alter',['missing','duplicate','other-foreign','missing-exception'])
def test_canonical_membership_never_silently_drops_or_replaces_native_samples(alter):
    records=fixture_records()
    if alter=='missing':
        records.pop(0)
    elif alter=='duplicate':
        records.append(records[0].copy())
    elif alter=='other-foreign':
        records.append(dict(path='Dataset/W7/15.5.TXT',bytes=9459))
    else:
        records.pop()
    with pytest.raises(ValueError):
        canonical_identities(records,EXCEPTION)
