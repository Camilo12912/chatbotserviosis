from flask import Flask, request
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# Variables de configuración
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Diccionario para manejar estados de los usuarios
user_states = {}

# Ruta para el webhook
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':  # Verificación inicial
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token de verificación inválido", 403

    elif request.method == 'POST':  # Mensajes entrantes
        data = request.json
        print(f"Datos recibidos del webhook: {data}")

        # Validar si hay mensajes
        if data and 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        value = change.get('value', {})
                        messages = value.get('messages', [])

                        for message in messages:
                            if 'text' in message:  # Si es un mensaje de texto
                                user_message = message['text']['body']
                                from_number = message['from']  # Número de quien envió el mensaje
                                reply = handle_message(user_message, from_number)  # Obtener respuesta
                                send_message(from_number, reply)  # Responder al usuario

        return "EVENT_RECEIVED", 200


def handle_message(user_message, from_number):
    """
    Lógica del chatbot basada en palabras clave y estados.
    """
    user_message = user_message.lower()

    # Obtener estado actual del usuario
    state = user_states.get(from_number, "menu")

    # Menú principal
    if state == "menu":
        if user_message in ['hola', 'menu', 'inicio']:
            return get_main_menu()

        # Opciones del menú principal
        if user_message in ['1', 'precio']:
            user_states[from_number] = "precios"
            return get_price_menu()
        elif user_message in ['2', 'soporte']:
            user_states[from_number] = "soporte"
            return "Por favor, comparte tu número de teléfono para que un asesor te llame en los próximos 10 minutos."
        elif user_message in ['3', 'problemas']:
            user_states[from_number] = "problemas"
            return "Por favor, comparte tu número de teléfono y correo electrónico para que un asesor se comunique contigo."

    # Submenú de precios
    elif state == "precios":
        if user_message == '1':
            return "El precio del *Tubo de ensayo estándar* es de $5,000 COP.\nEscribe *menu* para regresar al menú principal."
        elif user_message == '2':
            return "El precio del *Tubo de ensayo resistente al calor* es de $12,000 COP.\nEscribe *menu* para regresar al menú principal."
        elif user_message == '3':
            return "El precio del *Juego de tubos de ensayo (10 piezas)* es de $45,000 COP.\nEscribe *menu* para regresar al menú principal."
        elif user_message == "menu":
            user_states[from_number] = "menu"
            return get_main_menu()

    # Validación de soporte
    elif state == "soporte":
        if user_message.isdigit() and len(user_message) == 10:
            user_states[from_number] = "menu"
            return (
                "✅ Número registrado correctamente. Un asesor se comunicará contigo en breve.\n"
                "Escribe *menu* para regresar al menú principal."
            )

    # Validación de problemas
    elif state == "problemas":
        if "@" in user_message and "." in user_message:  # Validar correo
            user_states[from_number] = "menu"
            return (
                "✅ Problema registrado correctamente. Un asesor se comunicará contigo en breve.\n"
                "Escribe *menu* para regresar al menú principal."
            )

    # Respuesta genérica y reinicio al menú principal
    user_states[from_number] = "menu"
    return (
        "⚠️ Lo siento, no entendí tu mensaje.\n"
        "Escribe *menu* para regresar al menú principal o selecciona una opción del menú."
    )


def send_message(to_number, message):
    """
    Enviar un mensaje al usuario a través del API de WhatsApp.
    """
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Mensaje enviado correctamente a {to_number}: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje: {e}")
        if hasattr(e, 'response'):
            print(f"Respuesta completa: {e.response.text}")


def get_main_menu():
    """
    Devuelve el menú principal.
    """
    return (
        "🌟 *Menú Principal* 🌟\n"
        "1️⃣ *Precio*: Consulta los precios de nuestros productos.\n"
        "2️⃣ *Soporte*: Solicita asistencia técnica.\n"
        "3️⃣ *Problemas*: Reporta problemas con tu pedido.\n"
        "Por favor, responde con la palabra clave o el número de la opción que deseas."
    )


def get_price_menu():
    """
    Devuelve el submenú de precios.
    """
    return (
        "🔍 *Consulta de Precios*:\n"
        "1️⃣ Tubo de ensayo estándar\n"
        "2️⃣ Tubo de ensayo resistente al calor\n"
        "3️⃣ Juego de tubos de ensayo (10 piezas)\n"
        "Por favor, responde con el número del producto para conocer su precio o escribe *menu* para volver."
    )


if __name__ == '__main__':
    app.run(port=5000, debug=True)
