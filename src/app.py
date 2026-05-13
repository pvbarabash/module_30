from flask import Flask, jsonify, request
from module_30.src.models import db, Client, Parking, ClientParking
from datetime import datetime, timezone

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prod.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    register_routes(app)

    return app


def register_routes(app):
    @app.route('/clients', methods=['GET'])
    def get_clients():
        clients = Client.query.all()
        return jsonify([client.to_dict() for client in clients])

    @app.route('/clients/<int:client_id>', methods=['GET'])
    def get_client(client_id):
        client = Client.query.get_or_404(client_id)
        return jsonify(client.to_dict())


    @app.route('/clients', methods=['POST'])
    def create_client():
        data = request.get_json()

        if not data.get('name') or not data.get('surname'):
            return jsonify({'error': 'Name and surname are required'}), 400

        client = Client(
            name=data['name'],
            surname=data['surname'],
            credit_card=data.get('credit_card'),
            car_number=data.get('car_number')
        )

        db.session.add(client)
        db.session.commit()

        return jsonify(client.to_dict()), 201

    @app.route('/parkings', methods=['POST'])
    def create_parking():
        data = request.get_json()

        if not data.get('address') or 'count_places' not in data:
            return jsonify({'error': 'Address and count_places are required'}), 400

        parking = Parking(
            address=data['address'],
            opened=data.get('opened', True),
            count_places=data['count_places'],
            count_available_places=data.get('count_available_places', data['count_places'])
        )

        db.session.add(parking)
        db.session.commit()

        return jsonify(parking.to_dict()), 201


    @app.route('/client_parkings', methods=['POST'])
    def enter_parking():
        data = request.get_json()
        client_id = data.get('client_id')
        parking_id = data.get('parking_id')

        if not client_id or not parking_id:
            return jsonify({'error': 'client_id and parking_id are required'}), 400

        client = Client.query.get(client_id)
        parking = Parking.query.get(parking_id)

        if not parking:
            return jsonify({'error': 'Parking not found'}), 404
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        if not parking.opened:
            return jsonify({'error': 'Parking is closed'}), 400
        if parking.count_available_places <= 0:
            return jsonify({'error': 'No available places'}), 400
        if not client.credit_card:
            return jsonify({'error': 'Client has no credit card'}), 400

        existing = ClientParking.query.filter_by(
            client_id=client_id,
            parking_id=parking_id,
            time_out=None
        ).first()

        if existing:
            return jsonify({'error': 'Client is already on this parking'}), 400

        log_entry = ClientParking(
            client_id=client_id,
            parking_id=parking_id,
            time_in=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)

        parking.count_available_places -= 1

        db.session.commit()

        return jsonify(log_entry.to_dict()), 201


    @app.route('/client_parkings', methods=['DELETE'])
    def exit_parking():
        data = request.get_json()
        client_id = data.get('client_id')
        parking_id = data.get('parking_id')

        if not client_id or not parking_id:
            return jsonify({'error': 'client_id and parking_id are required'}), 400

        log_entry = ClientParking.query.filter_by(
            client_id=client_id,
            parking_id=parking_id,
            time_out=None
        ).first()

        if not log_entry:
            return jsonify({'error': 'Active entry not found'}), 404

        client = Client.query.get(client_id)
        if not client.credit_card:
            return jsonify({'error': 'Payment failed: no credit card'}), 400

        log_entry.time_out = datetime.now(timezone.utc)


        parking = Parking.query.get(parking_id)
        parking.count_available_places += 1

        db.session.commit()

        return jsonify({'message': 'Exit successful'}), 200


