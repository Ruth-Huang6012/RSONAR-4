#edit Jul 27 2023 Tim v2.3.8
#import
from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
#from pynq.overlays.base import BaseOverlay
#base = BaseOverlay("base.bit")
import time
#from pynq import Overlay
#from pynq.lib import MicroblazeLibrary
import socket
import os
from datetime import datetime
#from pynq.lib.arduino import Arduino_Analog
#from pynq.lib.pmod import Pmod_IIC
import sys
import glob
import serial

#Das Blinkenlights
#rgbleds = [base.rgbleds[i] for i in range(4, 6)]
#leds = [base.leds[i] for i in range(4)]

# Toggle board LEDs leaving small LEDs lit
#for i in range(8):
    #[l.off() for l in leds]
    #[rgbled.off() for rgbled in rgbleds]
    #sleep(.2)
    #[l.on() for l in leds]
    #[rgbled.on(1) for rgbled in rgbleds]
    #sleep(.2)

#[rgbled.off() for rgbled in rgbleds]

#Setup
#UART_RXD = 0 ## Arduino pin 0 is RXD
#UART_TXD = 1 ## Arduino pin 1 is TXD
#lib = MicroblazeLibrary(base.iop_arduino, ["uart"])
INPUT_PIN = 0
OUTPUT_PIN = 1
GPIO.setup(INPUT_PIN, GPIO.IN)
GPIO.setup(OUTPUT_PIN, GPIO.OUT)

strLength = 165 
countR=0

def comms():
    try:
        #sys.path.append(r'/home/xilinx/jupyter_notebooks/Comms/')
        from comms_params import SERVER, PORT, interval, folder_to_downlink, \
            img_text_file, gps_text_file, rtc_text_file, num_bytes, bytes_sleep, num_images
    except Exception as e:
        print(e)
        SERVER = '172.20.3.151'
        PORT = 5001
        interval = 1
        folder_to_downlink = '/downlink'
        img_text_file = 'commsDataKeeper.csv'
        gps_text_file = 'gps_log.txt'
        rtc_text_file = 'rtc_data.txt'
        num_bytes = 1
        bytes_sleep = 0.001
        num_images = 5

    def send_string(sock, string):
        sock.sendall(string.encode() + b'\n')

    def send_int(sock, integer):
        sock.sendall(str(integer).encode() + b'\n')

    def transmit(sock, folder, img_text_file, gps_text_file, rtc_text_file):
        cur_time = datetime.now()
        prefix = cur_time.strftime('_%Y_%m_%d_%H_%M_%S_')
        img_lines_to_send = ''
        try:
            with open(os.path.join(folder_to_downlink,img_text_file)) as file:
                for line in (file.readlines() [-10:]):
                    img_lines_to_send += line
        except FileNotFoundError as e:
            img_lines_to_send = "FileNotFoundError: " + str(e)
        img_text_to_send = prefix + img_text_file
        with open(os.path.join(folder, img_text_to_send), 'w') as f:
            f.write(img_lines_to_send)
        gps_lines_to_send = ''
        try:
            with open(os.path.join(folder_to_downlink,gps_text_file)) as file:
                for line in (file.readlines() [-10:]):
                    gps_lines_to_send += line
        except FileNotFoundError as e:
            gps_lines_to_send = "FileNotFoundError: " + str(e)
        gps_text_to_send = prefix + gps_text_file
        with open(os.path.join(folder, gps_text_to_send), 'w') as f:
            f.write(gps_lines_to_send)
        rtc_lines_to_send = ''
        try:
            with open(os.path.join(folder_to_downlink,rtc_text_file)) as file:
                for line in (file.readlines() [-10:]):
                    rtc_lines_to_send += line
        except FileNotFoundError as e:
            rtc_lines_to_send = "FileNotFoundError: " + str(e)
        rtc_text_to_send = prefix + rtc_text_file
        with open(os.path.join(folder, rtc_text_to_send), 'w') as f:
            f.write(rtc_lines_to_send)
        print(f'Sending folder: {folder}')
        send_string(sock, folder)
        all_files = os.listdir(folder)
        all_files = glob.glob('*.tif', root_dir=folder)
        all_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)))
        files = all_files[-num_images:]
        files.insert(0,gps_text_to_send)
        files.insert(0,rtc_text_to_send)
        files.insert(0,img_text_to_send)
        send_int(sock, len(files))
        # start_time = time.time()
        # total_bytes = 0
        for file in files:
            path = os.path.join(folder, file)
            try:
                filesize = os.path.getsize(path)
                # total_bytes += filesize
            except FileNotFoundError as e:
                print(e)
                continue
            print(f'Sending file: {file} ({filesize} bytes)')
            send_string(sock, file)
            send_int(sock, filesize)
            with open(path, 'rb') as f:
                while (byte := f.read(num_bytes)):
                    # send_start = time.time()
                    sock.sendall(byte)
                    # send_end = time.time()
                    # send_elapsed = send_end - send_start
                    # burst_speed = 8 / send_elapsed
                    # if burst_speed >= 300000:
                    #     print(f"Burst Speed: {burst_speed/1000:.3f} kbit/s")
                    # print("break")
                    time.sleep(bytes_sleep)
        # end_time = time.time()
        # total_bits = total_bytes * 8
        # elapsed_time = end_time - start_time
        # avg_speed = total_bits / elapsed_time
        # print(f"Elapsed time: {elapsed_time:.3f} s ({elapsed_time/60:.3f} min)")
        # print(f"Average Speed: {avg_speed/1000:.3f} kbit/s")

    while True:
        s = socket.socket()
        try:
            s.connect((SERVER, PORT))
        except Exception as e:
            print(e)
            time.sleep(10)
            continue
        with s:
            try:
                transmit(s, folder_to_downlink, img_text_file, gps_text_file, rtc_text_file)
            except Exception as e:
                print(e)
                pass
        time.sleep(interval*5)

##
##def read_gps():
##    raw=''
##    try:
##        inString = [0x00] * strLength
##        #GPS = lib.uart_open(UART_TXD, UART_RXD) 
##        GPS = GPIO.input(INPUT_PIN)
##        #GPS.read(inString, len(inString)) #void uart_read(uart dev_id, char* read_data, unsigned int length)
##        #GPS.close()
##        #raw=''
##        #for char in inString:# Hex to ascii
##            #raw = raw + chr(char)
##    except Exception as e:
##        filename = './gps/debug_log.txt'
##        GPSfile = open(filename, "a")
##        hold=str(e)
##        GPSfile.write(hold)
##        GPSfile.close()
##    return raw

##def gps():
##    filename = './gps/debug_log.txt'
##    GPSfile = open(filename, "a")
##    hold="Boot GPS"+"\n"
##    GPSfile.write(hold)
##    GPSfile.close()
##
##    countR=0 #raw lines
##    countC=0 #clean lines
##    while True:
##        raw = read_gps()
##        #filename = '/home/xilinx/mission_data/sensors/gps/raw_gps.txt'
##        #GPSfile = open(filename, "a")
##        z=0
##        for i in raw: #IDK why I did this this way
##            z+=1
##        if z>0:
##            #GPSfile = open(filename, "a")
##            #GPSfile.write(raw)
##            #GPSfile.close()
##            countR+=1
##
##            message=''
##            for char in raw:
##                if char !=13: #13= carrage return
##                    message = message + char
##            if ('$GNGGA' in message):
##                filename = './gps/gps_log.txt'
##                GPSfile = open(filename, "a+")
##                message=message+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()+read_gps()
##                fullyFiltered=''
##                go=True
##                step=0
##                for char in message:
##                    if (step>10 and char=='$'):  
##                        go=False
##                    elif (char!=13 and go==True):
##                        fullyFiltered=fullyFiltered+char
##                    else:
##                        go=False
##                    step+=1
##                full_msg_split = fullyFiltered.split(',') 
##                if len(full_msg_split) == 15:
##                    global timeGPS
##                    timeGPS = full_msg_split[1]
##                GPSfile.write(fullyFiltered)
##                GPSfile.close()
##
##                filename = './comms/gps_log.txt'
##                GPSfile = open(filename, "a+")
##                GPSfile.write(fullyFiltered)
##                GPSfile.close()
##
##                countC+=1
##
##        filename = './gps/debug_log.txt'
##        GPSfile = open(filename, "a")
##        hold="Raw Lines: "+str(countR)+"    Clean Lines: "+str(countC)+"\n"
##        GPSfile.write(hold)
##        GPSfile.close()
##
##def RTC_init(): #set up RTC
##    # Define the I2C address of the RTC
##    rtc_address = 0x68
##
##    # Initialize the Pmod IIC module (SDA = 7, SCL = 6)
##    try:
##        iic = Pmod_IIC(base.PMODB, 6, 7, rtc_address)
##    except:
##        print("Error: Can't initialize iic because of failure connection between PYNQ and RTC")    
##
##    # Set the current date and time for the RTC
##    now = datetime.now()
##
##    sec_tens = int(now.second / 10) << 4
##    sec_ones = now.second % 10
##    seconds_byte = sec_tens | sec_ones
##    min_tens = int(now.minute / 10) << 4
##    min_ones = now.minute % 10
##    minutes_byte = min_tens | min_ones
##    hour_tens = int(now.hour / 10) << 4
##    hour_ones = now.hour % 10
##    hour_byte = hour_tens | hour_ones
##    day_tens = int(now.day / 10) << 4
##    day_ones = now.day % 10
##    day_byte = day_tens | day_ones
##    mon_tens = int(now.month / 10) << 4
##    mon_ones = now.month % 10
##    month_byte = mon_tens | mon_ones
##    year_tens = int((now.year-2000) / 10) << 4
##    year_ones = (now.year-2000) % 10
##    year_byte = year_tens | year_ones
##
##    # Create "RTCData" folder if it doesn't exist
##    if not os.path.exists('./RTCData'):
##        os.makedirs('./RTCData')
##
##    # receive data from RTC for initializing    
##    try:
##        iic.send(bytearray([0x00]))
##        received_time = iic.receive(7)
##        year_tens = int.from_bytes([received_time[6]], byteorder='big') >> 4 & 0xF
##        year_ones = int.from_bytes([received_time[6]], byteorder='big') & 0xF
##        month_tens = int.from_bytes([received_time[5]], byteorder='big') >> 4 & 0xF
##        month_ones = int.from_bytes([received_time[5]], byteorder='big') & 0xF
##        day_tens = int.from_bytes([received_time[4]], byteorder='big') >> 4 & 0xF
##        day_ones = int.from_bytes([received_time[4]], byteorder='big') & 0xF
##        
##        year = year_tens * 10 + year_ones
##        month = month_tens * 10 + month_ones
##        day = day_tens * 10 + day_ones
##        
##    except:
##        print("Error: Can't send data to RTC because of failure connection between PYNQ and RTC")
##        
##    # initialize date if No date in RTC    
##    try:
##        if year + 2000 != now.year or month != now.month or day != now.day:
##            iic.send(bytearray([0x00, seconds_byte, minutes_byte, hour_byte, 0x00, day_byte, month_byte, year_byte]))
##            
##            # Open file for writing
##            file = open("/RTCData/rtc_data.txt", "a")
##            file.write('[RTC time]' + '           [Board time]' + '\n')
##            file.close()
##            
##    except:
##        print("Error: Can't send data to RTC because of failure connection between PYNQ and RTC")
##def RTC_track():
##    GPSfile = open("/RTCData/debug_rtc.txt", "a")
##    hold="Boot RTC_track"+"\n"
##    GPSfile.write(hold)
##
##    # Define the I2C address of the RTC
##    rtc_address = 0x68
##
##    # Initialize the Pmod IIC module (SDA = 7, SCL = 6)
##    iic = Pmod_IIC(base.PMODB, 6, 7, rtc_address)
##
##    # Create "RTCData" folder if it doesn't exist
##    if not os.path.exists('/RTCData'):
##        os.makedirs('/RTCData')
##
##    while True:
##        GPSfile = open("/RTCData/debug_rtc.txt", "a")
##        # Open file for append
##        file = open("/RTCData/rtc_data.txt", "a")
##
##        # Read current date and time from RTC
##        iic.send(bytearray([0x00]))
##        received_time = iic.receive(7)
##
##        # Convert data to datetime object
##        year_tens = int.from_bytes([received_time[6]], byteorder='big') >> 4 & 0xF
##        year_ones = int.from_bytes([received_time[6]], byteorder='big') & 0xF
##        month_tens = int.from_bytes([received_time[5]], byteorder='big') >> 4 & 0xF
##        month_ones = int.from_bytes([received_time[5]], byteorder='big') & 0xF
##        day_tens = int.from_bytes([received_time[4]], byteorder='big') >> 4 & 0xF
##        day_ones = int.from_bytes([received_time[4]], byteorder='big') & 0xF
##        hour_tens = int.from_bytes([received_time[2]], byteorder='big') >> 4 & 0xF
##        hour_ones = int.from_bytes([received_time[2]], byteorder='big') & 0xF
##        min_tens = int.from_bytes([received_time[1]], byteorder='big') >> 4 & 0xF
##        min_ones = int.from_bytes([received_time[1]], byteorder='big') & 0xF
##        sec_tens = int.from_bytes([received_time[0]], byteorder='big') >> 4 & 0xF
##        sec_ones = int.from_bytes([received_time[0]], byteorder='big') & 0xF
##
##        year = year_tens * 10 + year_ones + 2000
##        month = month_tens * 10 + month_ones
##        day = day_tens * 10 + day_ones
##        hour = hour_tens * 10 + hour_ones
##        minute = min_tens * 10 + min_ones
##        second = sec_tens * 10 + sec_ones
##
##        dt = datetime(year, month, day, hour, minute, second)
##
##        # Format date and time string
##        date_time_str = '{:%Y-%m-%d %H:%M:%S}'.format(dt)
##        global timeRTC
##        timeRTC=date_time_str
##
##        # Get current time from PYNQ
##        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
##
##        # Concatenate date and time strings
##        date_time_str += ', ' + current_time
##
##        # Write data to file
##        file.write(date_time_str + '\n')
##
##        hold="track write ln292"+"\n"
##        GPSfile.write(hold)
##        GPSfile.close()
##
##        # Print data to terminal
##        print(date_time_str)
##
##        # Close file
##        file.close()
##
##        filename = './comms/rtc_data.txt'
##        GPSfile = open(filename, "a+")
##        GPSfile.write(date_time_str + '\n')
##        GPSfile.close()
##
##        # Wait for one second
##        time.sleep(1)



def read_pats():
    raw=''
    try:
        #inString = [0x00] * strLength
        #GPS = lib.uart_open(UART_TXD, UART_RXD) 
        #PATS = GPIO.input(INPUT_PIN) ##DIFFERENT INPUT PIN
        # Setup serial connection
        ser = serial.Serial('/dev/tty',  9600, timeout=1)
        # Open serial port at 9600 baudrate
        if  ser.in_waiting >  0:
            line = ser.readline().decode('utf-8').rstrip()
        # Read a line and decode it from bytes to string
        # Print the line
            time.sleep(1)
        #PATS.read(inString, len(inString)) #void uart_read(uart dev_id, char* read_data, unsigned int length)
        ser.close()
        raw=''
        for char in line:# Hex to ascii
            raw = raw + chr(char)
    except Exception as e:
        filename = './PATS/debug_log.txt'
        PATSfile = open(filename, "a")
        hold=str(e)
        PATSfile.write(hold)
        PATSfile.close()
    return raw

def pats():
    filename = './gps/debug_log.txt'
    PATSfile = open(filename, "a")
    hold="Boot PATS"+"\n"
    PATSfile.write(hold)
    PATSfile.close()

    countR=0 #raw lines
    countC=0 #clean lines
    while True:
        raw = read_pats()
        #filename = '/home/xilinx/mission_data/sensors/gps/raw_gps.txt'
        #GPSfile = open(filename, "a")
        z=0
        for i in raw: #IDK why I did this this way
            z+=1
        if z>0:
            #GPSfile = open(filename, "a")
            #GPSfile.write(raw)
            #GPSfile.close()
            countR+=1

            message=''
            for char in raw:
                if char !=13: #13= carrage return
                    message = message + char
            if ('$GNGGA' in message):
                filename = './pats/pats_log.txt'
                PATSfile = open(filename, "a+")
                message=message+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read_pats()+read__pats()
                fullyFiltered=''
                go=True
                step=0
                for char in message:
                    if (step>10 and char=='$'):  
                        go=False
                    elif (char!=13 and go==True):
                        fullyFiltered=fullyFiltered+char
                    else:
                        go=False
                    step+=1
                full_msg_split = fullyFiltered.split(',') 
                if len(full_msg_split) == 15:
                    global timePATS
                    timePATS = full_msg_split[1]
                PATSfile.write(fullyFiltered)
                PATSfile.close()

                filename = './comms/pats_log.txt'
                PATSfile = open(filename, "a+")
                PATSfile.write(fullyFiltered)
                PATSfile.close()

                countC+=1

        filename = './pats/debug_log.txt'
        PATSfile = open(filename, "a")
        hold="Raw Lines: "+str(countR)+"    Clean Lines: "+str(countC)+"\n"
        PATSfile.write(hold)
        PATSfile.close()

def times():
    file = open("./gps/time_log.txt", "a")
    file.write('[Board time]'+'           [PATS time]'+'\n')
    file.close()
    time.sleep(1)
    while True:
        PItime = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        """try:
            global timeRTC
            timeRTC=str(timeRTC)
        except:
            timeRTC='0'
        """
        try:
            global timePATs
            timePATs=str(timePATs)
        except:
            timePATs='0'
        file = open("./gps/time_log.txt", "a")
        file.write(PItime+' , '+timePATS+'\n')
        file.close()

#main
#RTC_init()
from threading import Thread
Thread(target = gps).start() 
#Thread(target = RTC_track).start()
Thread(target = comms).start()
Thread(target = times).start()
Thread(target = pats).start()


GPIO.cleanup()
