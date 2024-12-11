from flask import Flask, request, jsonify
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO

app = Flask(__name__)

def create_excel(data):
    # Crear un DataFrame con los datos
    df = pd.DataFrame([{
        'Dispositivo': data['device']['name'] or data['device']['ident'],
        'Fecha y Hora': datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
        'Dirección': data['position']['address'],
        'Latitud': data['position']['latitude'],
        'Longitud': data['position']['longitude'],
        'Calidad GSM': f"{data['status']['gsm_quality']}% ({data['status']['gsm_status']})",
        'Batería': f"{data['status']['battery_level']}%",
        'Temperatura': f"{data['status']['temperature']}°C",
        'Humedad': f"{data['status']['humidity']}%",
        'Estado Geofence': 'Dentro de ' + data['geofence']['names'] if data['geofence']['inside'] else 'Fuera de geofence'
    }])
    
    # Guardar DataFrame en un buffer de memoria
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()

def send_email(data):
    try:
        device_name = data['device']['name'] or data['device']['ident']
        timestamp = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Crear el archivo Excel
        excel_content = create_excel(data)
        
        # Codificar el archivo Excel en base64
        encoded_file = base64.b64encode(excel_content).decode()

        # Crear el mensaje
        message = Mail(
            from_email=os.environ.get('EMAIL_FROM'),
            to_emails=os.environ.get('EMAIL_TO'),
            subject=f'Reporte de Ubicación - {device_name}',
            html_content=f'<p>Adjunto encontrará el reporte de ubicación para el dispositivo {device_name} generado el {timestamp}.</p>'
        )

        # Agregar el archivo Excel como adjunto
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_file)
        attachment.file_type = FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        attachment.file_name = FileName(f'reporte_ubicacion_{device_name}_{timestamp.replace(":", "-")}.xlsx')
        attachment.disposition = Disposition('attachment')
        message.attachment = attachment

        # Enviar el email
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





