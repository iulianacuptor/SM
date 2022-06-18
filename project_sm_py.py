
#import the libraries used
from http import server
import threading
import time
import RPi.GPIO as GPIO
import smtplib
import pigpio
from flask import Flask
from flask import render_template
from threading import Thread

#GPIO.setwarnings(False)

#create an instance of the pigpio library
pi = pigpio.pi()

#define the pin used by the Buzzer
#this pin will be used by the pigpio library
#which takes the pins in GPIO forms
#we will use GPIO18, which is pin 12
buzzer = 18

#set the pin used by the buzzer as OUTPUT
pi.set_mode(buzzer, pigpio.OUTPUT)



GPIO.setmode(GPIO.BOARD)

#we set the PIN40 as an output pin (green LED)
green_led=40
red_led=16

GPIO.setup(green_led, GPIO.OUT)
GPIO.setup(red_led,GPIO.OUT)
#define the pins used by the ultrasonic module
trig = 32
echo = 38
#set the trigger pin as OUTPUT and the echo as INPUT
GPIO.setup(trig, GPIO.OUT)
GPIO.setup(echo, GPIO.IN)


it_was_started=False
stop_running=True

#start SMTP server
try:
    serverSMTP=smtplib.SMTP('smtp.gmail.com',587)
    serverSMTP.starttls()
    serverSMTP.login("smarthomesm22","smPROJECT")
except KeyboardInterrupt:
    serverSMTP.quit()


def run_app():
    global serverSMTP
    guest=False

    #the green LED starts
    GPIO.output(green_led, GPIO.HIGH)

    while True:
        if(stop_running):
            break

        distance=get_distance()

        if(distance!=-1):
            if (distance < 100 ) :
                if(distance >=50):
                    GPIO.output(red_led, GPIO.HIGH)

                    pi.hardware_PWM(buzzer,500,500000)
                    time.sleep(0.1)

                    pi.hardware_PWM(buzzer,0,0)
                    time.sleep(0.05)

                else: #(distance < 50):



                    #turn on the buzzer at a frequency of
                    #1000Hz for a 50% duty cycle
                    pi.hardware_PWM(buzzer, 1000, 500000)
                    

                    GPIO.output(red_led, GPIO.HIGH)
                    time.sleep(0.2)

                    GPIO.output(red_led, GPIO.LOW)
                    time.sleep(0.2)

                   
                    # the owner will be notified only if he hasn't
                    # been notified yet
                    if guest==False:
                        print("Someone is near your house!")
                        #mail_sent=True
                        guest=True #the guest has been detected
                        msg="Someone is near your house at the distance of "+str(distance)+"  cm"
                        serverSMTP.sendmail("smarthomesm22@gmail.com","gursachi711@gmail.com",msg)
                        #send mail

            else: #distance > 100 cm
                # send notify only if a guest has already been at your house 
                pi.hardware_PWM(buzzer,0,0)
                GPIO.output(red_led, GPIO.LOW)

                if guest==True: 
                    print("The uninvited guest left.")
                    #mail_sent=False
                    guest=False
                    msg="The uninvited guest left. Now, he is at distance of "+str(distance)+ " cm from your house"
                    serverSMTP.sendmail("smarthomesm22@gmail.com","gursachi711@gmail.com",msg)

                    #send mail


        time.sleep(0.1)





def get_distance():

    #set the trigger to HIGH
    GPIO.output(trig, GPIO.HIGH)

    #sleep 0.00001 s and the set the trigger to LOW
    time.sleep(0.00001)

    #set the trigger to LOW
    GPIO.output(trig, GPIO.LOW)

    #save the start and stop times
    start = time.time()
    stop = time.time()

    #modify the start time to be the last time until
    #the echo becomes HIGH
    while GPIO.input(echo) == 0:
        start = time.time()
    #modify the stop time to be the last time until
    #the echo becomes LOW
    while GPIO.input(echo) == 1:
        stop = time.time()

    #get the duration of the echo pin as HIGH
    duration = stop - start

    #calculate the distance in cm
    distance = 34300/2 * duration

    #the reading can be erroneous, and we will print
    #the distance only if it is higher than the specified value
    if distance > 1:
        return distance
    else:
        return -1




app=Flask(__name__)

@app.route('/')
def index():
    return render_template('app.html')


myThread=threading.Thread(target=run_app)

@app.route('/stop',methods=['POST'])
def stop_app():

    if it_was_started:
    	global myThread
    	if(myThread.is_alive):
        	global stop_running
        	stop_running=True
        	myThread.join()
	


    GPIO.output(green_led, GPIO.LOW)
    #turn off the buzzer
    GPIO.output(red_led, GPIO.LOW)
    pi.hardware_PWM(buzzer,0,0)
    #pi.write(buzzer, 0)
    return render_template('app.html')



@app.route('/start',methods=['POST'])
def start_app():
    global it_was_started
    global stop_running
    global myThread

    if it_was_started:    	
    	if(myThread.is_alive):        	
            stop_running=True
            myThread.join()


    
    it_was_started=True
    stop_running=False

    runningThread=threading.Thread(target=run_app)
    
    myThread=runningThread
    myThread.start() 
    
    return render_template('app.html')
    



if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0')
    except:
        print("Some Error ")
    finally:
        
        serverSMTP.quit()
        pi.write(buzzer,0)
        GPIO.output(green_led, GPIO.LOW)
        GPIO.output(red_led, GPIO.LOW)
        GPIO.cleanup()

        pi.stop()

