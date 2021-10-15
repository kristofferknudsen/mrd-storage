
import re
import uuid
import logging

from datetime import datetime, timedelta

from flask import Blueprint
from flask_restful import Api, Resource
from flask_restful import fields, marshal

from flask import jsonify, request, make_response

from sqlalchemy.exc import NoResultFound

from ..version import version
from ..database import Session
from ..database import Blob as BlobEntry
from ..database import KeyValuePair


class Tags:
    @classmethod
    def output(cls, attr, obj):
        return dict(getattr(obj, attr))


_blob_marshal_fields = {
    'tags': Tags,
    'created': fields.DateTime,
    'timeout': fields.DateTime,
    'location': fields.Url(endpoint='v1.blobs_data_endpoint')
}


class Info(Resource):

    @classmethod
    def get(cls):
        return jsonify({
            'server': 'MRD Storage Server',
            'version': version
        })


class Blob(Resource):

    @classmethod
    def get(cls, id):

        try:
            session = Session()
            entry = session.query(BlobEntry).filter_by(id=id).one()
        except NoResultFound:
            return "", 404

        location = fields.Url(endpoint='v1.blobs_data_endpoint')

        response = make_response(entry.data)
        response.headers.update({
            'Content-Type': entry.type,
            'Content-Location': location.output('id', entry),
            'Last-Modified': entry.created,
            'x-mrd-tag-name': entry.name,
            'x-mrd-tag-device': entry.device,
            'x-mrd-tag-session': entry.session,
            'x-mrd-tag-subject': entry.subject
        })

        return response

    @classmethod
    def delete(cls, id):

        session = Session()
        session.query(BlobEntry).filter_by(id=id).delete()
        session.commit()

        return "", 200


class Blobs(Resource):

    @classmethod
    def get(cls):

        if 'subject' not in request.args:
            return "", 400

        # TODO: Pagination.
        results = Session() \
            .query(BlobEntry) \
            .filter_by(**request.args) \
            .order_by(BlobEntry.created.desc()) \
            .all()

        return marshal(results, _blob_marshal_fields, envelope='items')

    @classmethod
    def post(cls):

        if 'x-mrd-tag-name' not in request.headers:
            return "", 400

        if 'x-mrd-tag-subject' not in request.headers:
            return "", 400

        params = {}

        if 'content-type' in request.headers:
            params.update(type=request.headers.get('content-type'))

        tag_pattern = re.compile(r'x-mrd-tag-(?P<tag>.*)', flags=re.IGNORECASE)
        tags = {re.match(tag_pattern, header).group('tag').lower(): value
                for header, value in request.headers
                if re.match(tag_pattern, header)}

        if 'ttl' in tags:
            params.update(timeout=datetime.now() + timedelta(seconds=int(tags.pop('ttl'))))

        entry = BlobEntry(
            id=str(uuid.uuid4()),
            data=request.data,
            tags=[KeyValuePair(key=key, value=value) for key, value in tags.items()],
            **params
        )

        session = Session()
        session.add(entry)
        session.commit()

        return marshal(entry, _blob_marshal_fields), 201


class Latest(Resource):

    @classmethod
    def get(cls):
        pass


blueprint = Blueprint('v1', __name__, url_prefix='/v1')

api = Api(blueprint)
api.add_resource(Info, '/info')
api.add_resource(Blob, '/blobs/<id>', endpoint='blobs_data_endpoint')
api.add_resource(Blobs, '/blobs')
api.add_resource(Latest, '/blobs/latest')
