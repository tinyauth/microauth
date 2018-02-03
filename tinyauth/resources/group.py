from flask import Blueprint, jsonify, make_response, request
from flask_restful import Resource, abort, fields, marshal, reqparse

from tinyauth.api import Api
from tinyauth.app import db
from tinyauth.audit import audit_request, audit_request_cbv
from tinyauth.authorize import internal_authorize
from tinyauth.models import Group, User
from tinyauth.simplerest import build_response_for_request

group_fields = {
    'id': fields.Integer,
    'name': fields.String,
}

group_parser = reqparse.RequestParser()
group_parser.add_argument('name', type=str, location='json', required=True)

group_blueprint = Blueprint('group', __name__)


class GroupResource(Resource):

    def _get_or_404(self, group_id):
        group = Group.query.filter(Group.name == group_id).first()
        if not group:
            abort(404, message=f'group {group_id} does not exist')
        return group

    @audit_request_cbv('GetGroup')
    def get(self, audit_ctx, group_id):
        internal_authorize('GetGroup', f'arn:tinyauth:groups/{group_id}')

        group = self._get_or_404(group_id)
        audit_ctx['request.group'] = group.name
        return jsonify(marshal(group, group_fields))

    @audit_request_cbv('UpdateGroup')
    def put(self, audit_ctx, group_id):
        internal_authorize('UpdateGroup', f'arn:tinyauth:groups/{group_id}')

        args = group_parser.parse_args()

        group = self._get_or_404(group_id)
        audit_ctx['request.group'] = group.name
        group.name = args['name']
        db.session.add(group)

        db.session.commit()

        return jsonify(marshal(group, group_fields))

    @audit_request_cbv('DeleteGroup')
    def delete(self, audit_ctx, group_id):
        internal_authorize('DeleteGroup', f'arn:tinyauth:groups/{group_id}')

        group = self._get_or_404(group_id)
        audit_ctx['request.group'] = group.name
        db.session.delete(group)

        return make_response(jsonify({}), 201, [])


class GroupsResource(Resource):

    @audit_request_cbv('ListGroups')
    def get(self, audit_ctx):
        internal_authorize('ListGroups', f'arn:tinyauth:groups/')

        return build_response_for_request(Group, request, group_fields)

    @audit_request_cbv('CreateGroup')
    def post(self, audit_ctx):
        args = group_parser.parse_args()
        audit_ctx['request.group'] = args['name']

        internal_authorize('CreateGroup', f'arn:tinyauth:groups/args["name"]')

        group = Group(
            name=args['name'],
        )

        db.session.add(group)
        db.session.commit()

        return jsonify(marshal(group, group_fields))


@group_blueprint.route('/api/v1/groups/<group_id>/add-user', methods=['POST'])
@audit_request('AddUserToGroup')
def add_user_to_group(audit_ctx, group_id):
    internal_authorize('AddUserToGroup', f'arn:tinyauth:')

    group = Group.query.filter(Group.name == group_id).first()
    if not group:
        abort(404, message=f'group {group_id} does not exist')

    audit_ctx['request.group'] = group.name

    user_parser = reqparse.RequestParser()
    user_parser.add_argument('user', type=int, location='json', required=True)
    args = user_parser.parse_args()

    user = User.query.filter(User.id == args['user']).first()
    if not user:
        abort(404, message=f'user {args["user"]} does not exist')

    audit_ctx['request.username'] = user.username

    group.users.append(user)
    db.session.add(group)

    db.session.commit()

    return jsonify({})


@group_blueprint.route('/api/v1/groups/<group_id>/users/<user_id>', methods=['DELETE'])
@audit_request('RemoveUserFromGroup')
def remove_user_from_group(audit_ctx, group_id, user_id):
    internal_authorize('RemoveUserFromGroup', f'arn:tinyauth:')

    group = Group.query.filter(Group.name == group_id).first()
    if not group:
        abort(404, message=f'group {group_id} does not exist')

    audit_ctx['request.group'] = group.name

    user = User.query.filter(User.id == user_id).first()
    if not user:
        abort(404, message=f'user {user_id} does not exist')

    audit_ctx['request.username'] = user.username

    if user in group.users:
        group.users.remove(user)
        db.session.add(group)
        db.session.commit()

    return make_response(jsonify({}), 201, [])


group_api = Api(group_blueprint, prefix='/api/v1')
group_api.add_resource(GroupsResource, '/groups')
group_api.add_resource(GroupResource, '/groups/<group_id>')
