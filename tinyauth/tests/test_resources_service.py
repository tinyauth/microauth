import base64
import json

import jwt

from tinyauth.app import db
from tinyauth.audit import format_json
from tinyauth.models import Group, GroupPolicy, UserPolicy

from . import base


class TestCaseToken(base.TestCase):

    def test_authorize_service_invalid_outer_auth(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/authorize',
            data=json.dumps({
                'region': 'europe',
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:pword').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 401
        assert json.loads(response.get_data(as_text=True)) == {
            'errors': {'authorization': 'InvalidSignature'}
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 401,
            'request.legacy': True,
            'errors': {'authorization': 'InvalidSignature'},
        }

    def test_authorize_service_invalid_params(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/authorize',
            data=json.dumps({
                'region': 'europe',
                'action': 'myservice:LaunchRocket',
                'reesource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 400
        assert json.loads(response.get_data(as_text=True)) == {
            'errors': {
                'reesource': 'Unexpected argument',
                'resource': 'Missing required parameter in the JSON body'
            }
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 400,
            'request.legacy': True,
            'errors': {
                'reesource': 'Unexpected argument',
                'resource': 'Missing required parameter in the JSON body'
            }
        }

    def test_authorize_service(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/authorize',
            data=json.dumps({
                'region': 'europe',
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {'Authorized': True, 'Identity': 'charles'}

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.legacy': True,
            'request.permit': format_json({
                'myservice:LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': True,
            'response.identity': 'charles',
        }

    def test_authorize_service_by_group(self):
        with self.backend.app_context():
            group = Group(name='team')
            group.users.append(self.user)
            db.session.add(group)

            policy = GroupPolicy(name='myserver', group=group, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/authorize',
            data=json.dumps({
                'region': 'europe',
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {'Authorized': True, 'Identity': 'charles'}

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.legacy': True,
            'request.permit': format_json({
                'myservice:LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': True,
            'response.identity': 'charles',
        }

    def test_authorize_service_failure_no_user(self):
        response = self.client.post(
            '/api/v1/authorize',
            data=json.dumps({
                'region': 'europe',
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'nosuchuser:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': False,
            'ErrorCode': 'NoSuchKey',
            'Status': 401,
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.legacy': True,
            'request.permit': format_json({
                'myservice:LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': False,
        }

    def test_authorize_service_failure(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Deny',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/authorize',
            data=json.dumps({
                'region': 'europe',
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': False,
            'ErrorCode': 'NotPermitted',
            'Status': 403,
            'Identity': 'charles',
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.legacy': True,
            'request.permit': format_json({
                'myservice:LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': False,
            'response.identity': 'charles',
        }


class TestCaseTokenProxied(base.TestProxyMixin, TestCaseToken):
    pass


class TestCaseBatchToken(base.TestCase):

    def test_invalid_outer_auth(self):
        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permit': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:wrongpassword').decode('utf-8')
                ),
            },
            content_type='application/json',
        )
        assert response.status_code == 401
        assert json.loads(response.get_data(as_text=True)) == {
            'errors': {
                'authorization': 'InvalidSignature',
            }
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 401,
            'errors': {'authorization': 'InvalidSignature'},
            'request.service': 'myservice',
            'response.authorized': False,
        }

    def test_validate_input_failure(self):
        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permote': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                ),
            },
            content_type='application/json',
        )
        assert 'X-Request-Id' in response.headers
        assert response.status_code == 400
        assert json.loads(response.get_data(as_text=True)) == {
            'errors': {
                'permit': 'Missing required parameter in the JSON body',
                'permote': 'Unexpected argument',
            }
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 400,
            'errors': {
                'permit': 'Missing required parameter in the JSON body',
                'permote': 'Unexpected argument',
            },
            'request.service': 'myservice',
            'response.authorized': False,
        }

    def test_authorize_service(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permit': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': True,
            'Identity': 'charles',
            'Permitted': {'LaunchRocket': ['arn:myservice:rockets/thrift']},
            'NotPermitted': {},
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.permit': format_json({
                'LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': True,
            'response.identity': 'charles',
            'response.permitted': format_json({'LaunchRocket': ['arn:myservice:rockets/thrift']}),
            'response.not-permitted': format_json({}),
        }

    def test_authorize_service_by_group(self):
        with self.backend.app_context():
            group = Group(name='team')
            group.users.append(self.user)
            db.session.add(group)

            policy = GroupPolicy(name='myserver', group=group, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permit': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': True,
            'Identity': 'charles',
            'Permitted': {'LaunchRocket': ['arn:myservice:rockets/thrift']},
            'NotPermitted': {},
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.permit': format_json({
                'LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': True,
            'response.identity': 'charles',
            'response.permitted': format_json({'LaunchRocket': ['arn:myservice:rockets/thrift']}),
            'response.not-permitted': format_json({}),
        }

    def test_authorize_service_failure_no_user(self):
        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permit': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'nosuchkey:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': False,
            'ErrorCode': 'NoSuchKey',
            'NotPermitted': {'LaunchRocket': ['arn:myservice:rockets/thrift']},
            'Permitted': {},
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.region': 'europe',
            'request.permit': format_json({
                'LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': False,
            # 'response.identity': 'charles',
            'response.permitted': format_json({}),
            'response.not-permitted': format_json({'LaunchRocket': ['arn:myservice:rockets/thrift']}),
        }

    def test_authorize_service_failure_no_user_jwt(self):
        cookie = jwt.encode({
            'user': 'userdontexist',
            'iat': 0,
        }, 'dummycode')

        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permit': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Cookie', f'name={cookie}')
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': False,
            'ErrorCode': 'UnsignedRequest',
            'NotPermitted': {'LaunchRocket': ['arn:myservice:rockets/thrift']},
            'Permitted': {},
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.region': 'europe',
            'request.permit': format_json({
                'LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Cookie: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': False,
            # 'response.identity': 'charles',
            'response.permitted': format_json({}),
            'response.not-permitted': format_json({'LaunchRocket': ['arn:myservice:rockets/thrift']}),
        }

    def test_authorize_service_failure(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Deny',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        response = self.client.post(
            '/api/v1/services/myservice/authorize-by-token',
            data=json.dumps({
                'region': 'europe',
                'permit': {
                    'LaunchRocket': ['arn:myservice:rockets/thrift'],
                },
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': False,
            'ErrorCode': 'NotPermitted',
            'NotPermitted': {'LaunchRocket': ['arn:myservice:rockets/thrift']},
            'Permitted': {},
        }

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.region': 'europe',
            'request.permit': format_json({
                'LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': False,
            # 'response.identity': 'charles',
            'response.permitted': format_json({}),
            'response.not-permitted': format_json({'LaunchRocket': ['arn:myservice:rockets/thrift']}),
        }


class TestCaseBatchTokenProxied(base.TestProxyMixin, TestCaseBatchToken):

    def test_authorize_service_cached(self):
        with self.backend.app_context():
            policy = UserPolicy(name='myserver', user=self.user, policy={
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'myservice:*',
                    'Resource': '*',
                    'Effect': 'Allow',
                }]
            })
            db.session.add(policy)

            db.session.commit()

        for i in range(5):
            response = self.client.post(
                '/api/v1/services/myservice/authorize-by-token',
                data=json.dumps({
                    'region': 'europe',
                    'permit': {
                        'LaunchRocket': ['arn:myservice:rockets/thrift'],
                    },
                    'headers': [
                        ('Authorization', 'Basic {}'.format(
                            base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')))
                    ],
                    'context': {},
                }),
                headers={
                    'Authorization': 'Basic {}'.format(
                        base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                    )
                },
                content_type='application/json',
            )
            assert response.status_code == 200
            assert json.loads(response.get_data(as_text=True)) == {
                'Authorized': True,
                'Identity': 'charles',
                'Permitted': {'LaunchRocket': ['arn:myservice:rockets/thrift']},
                'NotPermitted': {},
            }

            # This asserts that the first call to authorize hits the upstream tinyauth
            # It also asserts that the next 4 do not, thus proving caching works
            assert len(self.app.auth_backend.session.get.call_args_list) == 4

        args, kwargs = self.audit_log.call_args_list[-1]
        assert args[0] == 'AuthorizeByToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.permit': format_json({
                'LaunchRocket': ['arn:myservice:rockets/thrift'],
            }),
            'request.region': 'europe',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': True,
            'response.identity': 'charles',
            'response.permitted': format_json({'LaunchRocket': ['arn:myservice:rockets/thrift']}),
            'response.not-permitted': format_json({}),
        }


class TestCaseLogin(base.TestCase):

    def test_authorize_service(self):
        policy = UserPolicy(name='myserver', user=self.user, policy={
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'myservice:*',
                'Resource': '*',
                'Effect': 'Allow',
            }]
        })
        db.session.add(policy)

        db.session.commit()

        response = self.client.post(
            '/api/v1/authorize-login',
            data=json.dumps({
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'charles:mrfluffy').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {'Authorized': True, 'Identity': 'charles'}

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'AuthorizeByLogin'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.permit': format_json({
                'myservice:LaunchRocket': ['arn:myservice:rockets/thrift']
            }),
            'request.region': 'global',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': True,
            'response.identity': 'charles',
        }

    def test_authorize_service_failure(self):
        policy = UserPolicy(name='myserver', user=self.user, policy={
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'myservice:*',
                'Resource': '*',
                'Effect': 'Deny',
            }]
        })
        db.session.add(policy)

        db.session.commit()

        response = self.client.post(
            '/api/v1/authorize-login',
            data=json.dumps({
                'action': 'myservice:LaunchRocket',
                'resource': 'arn:myservice:rockets/thrift',
                'headers': [
                    ('Authorization', 'Basic {}'.format(
                        base64.b64encode(b'charles:mrfluffy').decode('utf-8')))
                ],
                'context': {},
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        assert json.loads(response.get_data(as_text=True)) == {
            'Authorized': False,
            'ErrorCode': 'NotPermitted',
            'Identity': 'charles',
            'Status': 403
        }

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'AuthorizeByLogin'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.permit': format_json({
                'myservice:LaunchRocket': ['arn:myservice:rockets/thrift']
            }),
            'request.region': 'global',
            'request.actions': ['myservice:LaunchRocket'],
            'request.resources': ['arn:myservice:rockets/thrift'],
            'request.headers': ['Authorization: ** NOT LOGGED **'],
            'request.context': {},
            'response.authorized': False,
            'response.identity': 'charles',
        }


class TestCaseLoginToToken(base.TestCase):

    def test_authorize_service(self):
        policy = UserPolicy(name='myserver', user=self.user, policy={
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'myservice:*',
                'Resource': '*',
                'Effect': 'Allow',
            }]
        })
        db.session.add(policy)

        db.session.commit()

        response = self.client.post(
            '/api/v1/services/myservice/get-token-for-login',
            data=json.dumps({
                'username': 'charles',
                'password': 'mrfluffy',
                'csrf-strategy': 'header-token',
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        payload = json.loads(response.get_data(as_text=True))
        assert 'token' in payload
        assert 'csrf' in payload

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'GetTokenForLogin'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.service': 'myservice',
            'request.username': 'charles',
            'request.csrf-strategy': 'header-token',
        }

    def test_authorize_service_failure(self):
        policy = UserPolicy(name='myserver', user=self.user, policy={
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'myservice:*',
                'Resource': '*',
                'Effect': 'Deny',
            }]
        })
        db.session.add(policy)

        db.session.commit()

        response = self.client.post(
            '/api/v1/services/myservice/get-token-for-login',
            data=json.dumps({
                'username': 'charles',
                'password': 'password',
                'csrf-strategy': 'header-token',
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 401
        assert json.loads(response.get_data(as_text=True)) == {
            'errors': {'authentication': 'Invalid credentials'}
        }

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'GetTokenForLogin'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 401,
            'request.service': 'myservice',
            'errors': {'authentication': 'Invalid credentials'},
            'request.username': 'charles',
            'request.csrf-strategy': 'header-token',
        }


class TestGetServiceUserSigningToken(base.TestCase):

    def test_get_signing_token(self):
        response = self.client.get(
            '/api/v1/regions/europe/services/myservice/user-signing-tokens/charles/jwt/20170316',
            data=json.dumps({
                'username': 'charles',
                'password': 'mrfluffy',
                'csrf-strategy': 'header-token',
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        payload = json.loads(response.get_data(as_text=True))
        assert 'key' in payload
        assert 'identity' in payload

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'GetServiceUserSigningToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.region': 'europe',
            'request.service': 'myservice',
            'request.user': 'charles',
            'request.date': '20170316',
            'request.protocol': 'jwt',
        }


class TestGetServiceAccessKeySigningToken(base.TestCase):

    def test_get_signing_token(self):
        response = self.client.get(
            '/api/v1/regions/europe/services/myservice/access-key-signing-tokens/AKIDEXAMPLE/basic-auth/20170316',
            data=json.dumps({
                'username': 'charles',
                'password': 'mrfluffy',
                'csrf-strategy': 'header-token',
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        payload = json.loads(response.get_data(as_text=True))
        assert 'key' in payload
        assert 'identity' in payload

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'GetServiceAccessKeySigningToken'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.region': 'europe',
            'request.service': 'myservice',
            'request.access-key': 'AKIDEXAMPLE',
            'request.date': '20170316',
            'request.protocol': 'basic-auth',
        }


class TestGetServiceUserPolicies(base.TestCase):

    def test_get_signing_token(self):
        response = self.client.get(
            '/api/v1/regions/europe/services/myservice/user-policies/charles',
            data=json.dumps({
                'username': 'charles',
                'password': 'mrfluffy',
                'csrf-strategy': 'header-token',
            }),
            headers={
                'Authorization': 'Basic {}'.format(
                    base64.b64encode(b'AKIDEXAMPLE:password').decode('utf-8')
                )
            },
            content_type='application/json',
        )
        assert response.status_code == 200
        payload = json.loads(response.get_data(as_text=True))
        assert 'Statement' in payload

        args, kwargs = self.audit_log.call_args_list[0]
        assert args[0] == 'GetServiceUserPolicies'
        assert kwargs['extra'] == {
            'request-id': 'a823a206-95a0-4666-b464-93b9f0606d7b',
            'http.status': 200,
            'request.region': 'europe',
            'request.service': 'myservice',
            'request.user': 'charles',
        }
