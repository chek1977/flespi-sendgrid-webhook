from flask import Flask, request, jsonify
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

app = Flask(__name__)

def send_email(data):
    try:
        # Formatear el contenido del email
        device_name = data['device']['name'] or data['device']['ident']
        timestamp = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        html_content = f"""
        <h2>Reporte de Ubicación - {device_name}</h2>
        <p><strong>Fecha y Hora:</strong> {timestamp}</p>
        
        <h3>Ubicación</h3>
        <p><strong>Dirección:</strong> {data['position']['address']}</p>
        <p><strong>Coordenadas:</strong> {data['position']['latitude']}, {data['position']['longitude']}</p>
        
        <h3>Estado del Dispositivo</h3>
        <p><strong>Calidad GSM:</strong> {data['status']['gsm_quality']}% ({data['status']['gsm_status']})</p>
        <p><strong>Batería:</strong> {data['status']['battery_level']}%</p>
        <p><strong>Temperatura:</strong> {data['status']['temperature']}°C</p>
        <p><strong>Humedad:</strong> {data['status']['humidity']}%</p>
        
        <h3>Geofence</h3>
        <p><strong>Dentro de:</strong> {data['geofence']['names'] if data['geofence']['inside'] else 'Fuera de geofence'}</p>
        """

        message = Mail(
            from_email=os.environ.get('EMAIL_FROM'),
            to_emails=os.environ.get('EMAIL_TO'),
            subject=f'Ubicación Actual - {device_name}',
            html_content=html_content
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        
        # Enviar email
        if send_email(data):
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send email'}), 500

    return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))




