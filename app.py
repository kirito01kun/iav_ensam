from flask import *
import threading
import os
import RPi.GPIO as GPIO
import time

 
app = Flask(__name__)

calculated_water_level = 100
gps_val = [33.969246, -6.876551]

# Configure GPIO pins for sensors 
SENSOR_PINS = [17, 18, 22, 23]

# Configure GPIO pin for servo motor
SERVO_PIN = 27  # Example GPIO pin, adjust as needed

# Define GPIO setup
GPIO.setmode(GPIO.BCM)
for pin in SENSOR_PINS:
    GPIO.setup(pin, GPIO.IN)

GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)


def update_servo_angle(angle):
    global pwm
    duty_cycle = (angle / 18) + 2  # Map angle to duty cycle (2 to 12)
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(1)  # Let the servo move to the desired angle
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(0)

# GPIO cleanup
def cleanup_gpio():
    pwm.stop()
    GPIO.cleanup()

@app.route('/')
def index():
    return render_template('index.html', calculated_water_level=calculated_water_level)

@app.route('/shutdown', methods=['GET'])
def shutdown():
    print("Shutting down the server...")
    cleanup_gpio()
    os._exit(0)


def handler():
    global calculated_water_level
    while True:
        # Read digital presence sensors and update calculated_water_level
        s1 = GPIO.input(SENSOR_PINS[0])
        s2 = GPIO.input(SENSOR_PINS[1])
        s3 = GPIO.input(SENSOR_PINS[2])
        s4 = GPIO.input(SENSOR_PINS[3])
        s = s1 + s2 + s3 + s4
        if s == 0:
            calculated_water_level = 99
        elif s == 1:
            calculated_water_level = 75
        elif s == 2:
            calculated_water_level = 50
        elif s == 3:
            calculated_water_level = 25
        else:
            calculated_water_level = 0
        
        
        time.sleep(2)


@app.route('/get_water_level')
def get_water_level():
    global calculated_water_level
    return jsonify({'water_level': calculated_water_level})

@app.route('/get_gps_values')
def get_gps_values():
    global gps_val
    return jsonify({'latitude': gps_val[0], 'longitude': gps_val[1]})

@app.route('/update_percentage', methods=['POST'])
def update_percentage():
    new_percentage = int(request.form.get('percentage'))
    print(new_percentage)

    if new_percentage == 0:
        angle = 30
    elif new_percentage == 25:
        angle = 55
    elif new_percentage == 50:
        angle = 65
    elif new_percentage == 75:
        angle = 70
    elif new_percentage == 100:
        angle = 80
    else:
        angle = 30

    update_servo_angle(angle)
    
    return "Percentage & servo updated", 200


if __name__ == '__main__':
    handler_thread = threading.Thread(target=handler)
    handler_thread.start()
    app.run(debug=True, host='0.0.0.0')