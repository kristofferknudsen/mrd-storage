
import time
import pytest

from mrd.storage.wsgi import create_app


@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'DATABASE': "sqlite://"})
    with app.test_client() as client:
        yield client


def test_store_small_blob(client):

    response = client.post(
        '/v1/blobs',
        headers={
            'x-mrd-tag-name': 'short-test-data',
            'x-mrd-tag-device': 'test-device',
            'x-mrd-tag-session': 'test-session',
            'x-mrd-tag-subject': 'test-subject',
            'x-mrd-tag-ttl': 60,
        },
        data=b'This is a short byte string.'
    )

    import pprint
    print("\n\n")
    pprint.pprint(response.json)

    assert response.status_code == 201
    assert all(key in response.json
               for key in ['tags', 'created', 'timeout', 'location'])


def test_store_and_fetch_blob(client):

    data = b'Some bytes.'

    response = client.post(
        '/v1/blobs',
        headers={
            'x-mrd-tag-name': 'read-write-test-bytes',
            'x-mrd-tag-device': 'test-device',
            'x-mrd-tag-session': 'test-session',
            'x-mrd-tag-subject': 'test-subject',
            'x-mrd-tag-ttl': 60,
        },
        data=data
    )

    assert response.status_code == 201
    assert 'location' in response.json

    response = client.get(
        response.json.get('location')
    )

    assert response.status_code == 200
    assert response.data == data


def test_store_nameless_blob_not_allower(client):

    response = client.post(
        '/v1/blobs',
        headers={
            # x-mrd-tag-name is missing
            'x-mrd-tag-device': 'test-device',
            'x-mrd-tag-session': 'test-session',
            'x-mrd-tag-subject': 'test-subject',
            'x-mrd-tag-ttl': 60,
        },
        data=b''
    )

    assert response.status_code == 400  # Bad request


def test_bad_fetch_returns_not_found(client):

    response = client.get(
        '/v1/blob/missing-id'
    )

    assert response.status_code == 404


def test_store_with_partial_keys(client):

    data = b'Partial keys should be fine. Name is required though.'

    response = client.post(
        '/v1/blobs',
        headers={
            'x-mrd-tag-name': 'name-is-required',
            'x-mrd-tag-subject': 'subject-is-required'
        },
        data=data
    )

    assert response.status_code == 201
    assert 'location' in response.json

    response = client.get(
        response.json.get('location')
    )

    assert response.status_code == 200
    assert response.data == data


def test_store_and_search_with_unicode_keys(client):

    data = u"life ← {⊃1 ⍵ ∨.∧ 3 4 = +/ +⌿ ¯1 0 1 ∘.⊖ ¯1 0 1 ⌽¨ ⊂⍵}"
    name = u'श्रीमद्भगवद्गीता'
    device = u'🤝'
    session = u'😲'
    subject = u'👍'

    response = client.post(
        '/v1/blobs',
        headers={
            'x-mrd-tag-name': name,
            'x-mrd-tag-device': device,
            'x-mrd-tag-session': session,
            'x-mrd-tag-subject': subject,
            'x-mrd-tag-ttl': 60,
        },
        data=data.encode('utf-8')
    )

    assert response.status_code == 201
    assert 'location' in response.json

    search = client.get(
        '/v1/blobs',
        query_string={
            'name': name,
            'device': device,
            'session': session,
            'subject': subject
        }
    )

    assert search.status_code == 200
    assert 'items' in search.json
    assert all(result.get('location') == response.json.get('location') for result in search.json.get('items'))

    response = client.get(response.json.get('location'))

    assert response.status_code == 200
    assert response.data.decode('utf-8') == data


def test_store_and_search_multiple_results(client):

    def store_blob(name, data):
        result = client.post(
            '/v1/blobs',
            headers={
                'x-mrd-tag-name': name,
                'x-mrd-tag-device': 'search-test-device',
                'x-mrd-tag-session': 'search-test-session',
                'x-mrd-tag-subject': 'search-test-subject'
            },
            data=data
        )
        assert result.status_code == 201

    def search(**query):
        response = client.get('/v1/blobs', query_string=query)
        assert response.status_code == 200
        return response.json.get('items')

    store_blob('search-test-one', b'search-test-one')
    store_blob('search-test-two', b'search-test-two')
    store_blob('search-test-three', b'search-test-three')
    store_blob('search-test-four', b'search-test-four')

    assert len(search(device='search-test-device', subject='search-test-subject')) == 4
    assert len(search(session='search-test-session', subject='search-test-subject')) == 4

    results = search(device='search-test-device', session='search-test-session', subject='search-test-subject')

    # We better make sure the results are descending as well.
    assert all(earlier.get('created') >= later.get('created') for earlier, later in zip(results, results[1:]))
    assert [result.get('name') for result in results] == [
        'search-test-four',
        'search-test-three',
        'search-test-two',
        'search-test-one'
    ]


def test_search_with_no_filters_is_not_allowed(client):

    response = client.get('/v1/blobs')

    assert response.status_code == 400


def test_search_with_bad_filter_not_allowed(client):

    response = client.get(
        '/v1/blobs',
        query_string={
            'illegal_parameter': 'fun!'
        }
    )

    assert response.status_code == 400  # Bad Request


def test_delete_blob_deletes_blob(client):

    name = 'delete-test-blob-name'
    subject = 'delete-test-blob-subject'

    response = client.get('/v1/blobs', query_string={'name': name, 'subject': subject})

    assert response.status_code == 200
    assert not response.json.get('items')

    response = client.post(
        '/v1/blobs',
        headers={
            'x-mrd-tag-name': name,
            'x-mrd-tag-subject': subject
        },
        data=b'DELETE'
    )

    assert response.status_code == 201
    assert 'location' in response.json

    location = response.json.get('location')

    response = client.get('/v1/blobs', query_string={'name': name, 'subject': subject})

    assert response.status_code == 200
    assert response.json.get('items')

    response = client.get(location)

    assert response.status_code == 200
    assert response.data == b'DELETE'

    response = client.delete(location)

    assert response.status_code == 200

    response = client.get(location)

    assert response.status_code == 404


def test_latest_endpoint_single_blob(client):
    pass


def test_latest_endpoint_multiple_blobs(client):
    pass
