#!/usr/bin/env python
# coding=utf-8


from mock import MagicMock
from pytest import fixture, mark


@fixture
def mock_session_request():
    from requests.models import Response, Request

    response = MagicMock(spec=Response)
    response.status_code = 200

    session_request = MagicMock(spec=Request)
    session_request.response = response
    session_request.return_value = response
    # session_request.status_code = 200

    return session_request


@fixture
def patch_requests(monkeypatch, mock_session_request):
    import json

    def pickle_dumps(value):
        obj = {
            'status_code': value.status_code
        }
        return json.dumps(obj)

    def pickle_loads(value):
        try:
            value_string = value.decode("utf-8")
        except AttributeError:
            value_string = str(value)

        obj = json.loads(value_string)
        mock_session_request.response.status_code = obj.get('status_code')
        return mock_session_request

    monkeypatch.setattr('cache_requests._compat.pickle.dumps', pickle_dumps)
    monkeypatch.setattr('cache_requests._compat.pickle.loads', pickle_loads)
    monkeypatch.setattr('requests.sessions.Session.request', mock_session_request)


@fixture
def requests():
    from cache_requests.sessions import Session

    return Session()


@mark.usefixtures('patch_requests')
def test_requests_get(requests, mock_session_request):
    mock_session_request.assert_not_called()
    # 1st unique call
    requests.get('http://google.com')
    assert mock_session_request.call_count == 1
    requests.get('http://google.com')
    requests.get('http://google.com')
    assert mock_session_request.call_count == 1

    headers = {
        "accept-encoding": "gzip, deflate, sdch",
        "accept-language": "en-US,en;q=0.8"
    }
    payload = dict(sourceid="chrome-instant", ion="1", espv="2", ie="UTF-8", client="ubuntu",
                   q="hash%20a%20dictionary%20python")
    # 2nd unique call
    requests.get('http://google.com/search', headers=headers, params=payload)
    assert mock_session_request.call_count == 2
    requests.get('http://google.com/search', headers=headers, params=payload)
    requests.get('http://google.com/search', headers=headers, params=payload)
    requests.get('http://google.com/search', headers=headers, params=payload)
    requests.get('http://google.com/search', headers=headers, params=payload)
    assert mock_session_request.call_count == 2

    payload = dict(sourceid="chrome-instant", ion="1", espv="2", ie="UTF-8", client="ubuntu",
                   q="hash%20a%20dictionary%20python2")
    # 3rd unique call
    requests.get('http://google.com/search', headers=headers, params=payload)
    assert mock_session_request.call_count == 3
    requests.get('http://google.com/search', headers=headers, params=payload)
    assert mock_session_request.call_count == 3


@mark.usefixtures('patch_requests')
def test_requests_options(requests, mock_session_request):
    mock_session_request.assert_not_called()
    requests.options('http://google.com')
    requests.options('http://google.com')
    assert mock_session_request.call_count == 1
    assert mock_session_request.call_args == (('OPTIONS', 'http://google.com'), dict(allow_redirects=True))


@mark.usefixtures('patch_requests')
def test_requests_head(requests, mock_session_request):
    mock_session_request.assert_not_called()
    requests.head('http://google.com')
    requests.head('http://google.com')
    assert mock_session_request.call_count == 1

    assert mock_session_request.call_args == (('HEAD', 'http://google.com'), dict(allow_redirects=False))


@mark.usefixtures('patch_requests')
def test_requests_post(requests, mock_session_request):
    requests.cache.post = True

    mock_session_request.assert_not_called()
    requests.post('http://google.com')
    requests.post('http://google.com')
    assert mock_session_request.call_count == 1
    mock_session_request.assert_called_with('POST', 'http://google.com', data=None, json=None)


@mark.usefixtures('patch_requests')
def test_requests_put(requests, mock_session_request):
    requests.cache.put = True

    mock_session_request.assert_not_called()
    requests.put('http://google.com')
    requests.put('http://google.com')
    assert mock_session_request.call_count == 1
    mock_session_request.assert_called_with('PUT', 'http://google.com', data=None)


@mark.usefixtures('patch_requests')
def test_requests_patch(requests, mock_session_request):
    requests.cache.patch = True

    mock_session_request.assert_not_called()
    requests.patch('http://google.com')
    requests.patch('http://google.com')
    assert mock_session_request.call_count == 1
    mock_session_request.assert_called_with('PATCH', 'http://google.com', data=None)


@mark.usefixtures('patch_requests')
def test_requests_delete(requests, mock_session_request):
    requests.cache.delete = True

    mock_session_request.assert_not_called()
    requests.delete('http://google.com')
    requests.delete('http://google.com')
    assert mock_session_request.call_count == 1
    mock_session_request.assert_called_with('DELETE', 'http://google.com')


@mark.usefixtures('patch_requests')
def test_memoize_toggled_off(requests, mock_session_request):
    requests.cache.get = False

    mock_session_request.assert_not_called()
    requests.get('http://google.com')
    requests.get('http://google.com')
    assert mock_session_request.call_count == 2


# @mark.skipif
@mark.usefixtures('patch_requests')
def test_only_cache_200_response(requests, redis_mock, mock_session_request):
    def call_count():
        return redis_mock.get.call_count, redis_mock.set.call_count

    requests.get.connection = redis_mock

    redis_mock.assert_not_called()
    assert call_count() == (0, 0)

    requests.get('http://google.com')
    requests.get('http://google.com')

    assert call_count() == (2, 1)

    mock_session_request.response.status_code = 404

    requests.get('http://google.com', bust_cache=True)
    requests.get('http://google.com')

    assert call_count() == (3, 1)

    mock_session_request.response.status_code = 200

    requests.get('http://google.com')
    requests.get('http://google.com')

    assert call_count() == (5, 2)
